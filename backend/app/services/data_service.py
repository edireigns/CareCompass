"""Repeatable, transactional CMS imports. Suppressed values remain unknown."""
import csv
import hashlib
import json
import math
import threading
import uuid
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from sqlalchemy import func, text
from sqlalchemy.orm import selectinload
from app.db.session import Base, SessionLocal, engine
from app.models.hospital import Hospital, Location, HospitalQuality, HospitalOutcomes, PatientExperience, WaitTimeEstimate, Specialty, Insurance
from app.models.data import HospitalMeasure, DirectoryEntry, ImportRun, HospitalPresence

DATA_DIR = Path(__file__).resolve().parents[1] / 'data' / 'cms'
SOURCES = {
    'general': ('Hospital directory', 'Hospital_General_Information.csv', 'xubh-q36u'),
    'experience': ('Patient experience', 'HCAHPS-Hospital.csv', 'dgck-syfz'),
    'outcomes': ('Complications and mortality', 'Complications_and_Deaths-Hospital.csv', 'ynj2-r877'),
    'infections': ('Infection ratios', 'Healthcare_Associated_Infections-Hospital.csv', '77hc-ibv8'),
    'readmissions': ('Readmissions', 'Unplanned_Hospital_Visits-Hospital.csv', '632h-zaca'),
    'timely': ('Historical ED visit duration', 'Timely_and_Effective_Care-Hospital.csv', 'yv7e-xc69'),
    'coordinates': ('Census address coordinates', 'Hospital_Coordinates.csv', None),
}
refresh_lock = threading.Lock()
HC_FIELDS = {'H_HSP_RATING_9_10':'overall_satisfaction','H_RECMND_DY':'would_recommend_pct','H_COMP_1_A_P':'communication_score','H_CLEAN_HSP_A_P':'cleanliness_score'}
TYPE_SPECIALTIES = {'Psychiatric':'Psychiatry','Childrens':'Pediatrics','Long-term':'Long-term hospital care'}

def number(value):
    try:
        result = float(str(value).strip().replace(',', ''))
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None

def source_url(key):
    ident = SOURCES[key][2]
    return f'https://data.cms.gov/provider-data/dataset/{ident}' if ident else 'https://geocoding.geo.census.gov/'

def read_rows(path, required):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'{path.name}: required columns are missing: {sorted(required)}')
        rows = list(reader)
    if not rows:
        raise ValueError(f'{path.name} contains no records; previous data was preserved.')
    return rows

def download_source(key, folder=DATA_DIR):
    _, filename, ident = SOURCES[key]
    if not ident:
        return
    with httpx.Client(timeout=120, follow_redirects=False) as client:
        response = client.get(f'https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{ident}')
        response.raise_for_status()
        metadata = response.json()
        distributions = metadata.get('distribution', [])
        url = next(d['downloadURL'] for d in distributions if d.get('mediaType') == 'text/csv')
        if urlsplit(url).scheme != 'https' or urlsplit(url).hostname != 'data.cms.gov':
            raise ValueError('CMS returned an unexpected download host.')
        target = folder / filename
        temporary = target.with_suffix('.download')
        try:
            size = 0
            with client.stream('GET', url) as stream, temporary.open('wb') as output:
                stream.raise_for_status()
                for chunk in stream.iter_bytes():
                    size += len(chunk)
                    if size > 200_000_000:
                        raise ValueError('Dataset exceeds the 200 MB limit.')
                    output.write(chunk)
            read_rows(temporary, {'Facility ID'})
            temporary.replace(target)
            provenance = dict(sha256=hashlib.sha256(target.read_bytes()).hexdigest(), downloaded_on=date.today().isoformat(), release_date=metadata.get('modified'), dataset_id=ident, download_url=url)
            target.with_suffix('.metadata.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
        finally:
            temporary.unlink(missing_ok=True)

def measure_record(row, key, hospital_id):
    mid = row.get('Measure ID') or row.get('HCAHPS Measure ID', '')
    value = number(row.get('HCAHPS Answer Percent') if key == 'experience' else row.get('Score'))
    if value is None:
        return None
    if key == 'experience':
        if mid not in HC_FIELDS and mid != 'H_COMP_2_A_P': return None
        unit = '%'
    elif key == 'outcomes':
        if mid.startswith('MORT_') or mid in {'Hybrid_HWM','COMP_HIP_KNEE'}: unit = '%'
        elif mid == 'PSI_90': unit = 'composite index'
        elif mid.startswith('PSI_'): unit = 'per 1,000 discharges'
        else: return None
    elif key == 'infections':
        if not mid.endswith('_SIR'): return None
        unit = 'observed / expected ratio'
    elif key == 'readmissions':
        if not mid.startswith('READM_30_') and mid not in {'Hybrid_HWR','READM_30_HOSP_WIDE'}: return None
        unit = '%'
    elif key == 'timely':
        if mid not in {'OP_18a','OP_18b','OP_18c','OP_18d'}: return None
        unit = 'minutes (historical median)'
    else:
        return None
    if value < 0 or (unit == '%' and value > 100): return None
    return dict(id=str(uuid.uuid4()),hospital_id=hospital_id,source_key=key,measure_id=mid,
        name=row.get('Measure Name') or row.get('HCAHPS Question') or mid,value=value,unit=unit,
        comparison=row.get('Compared to National'),period_start=row.get('Start Date'),period_end=row.get('End Date'),source_url=source_url(key))

def import_general(db, rows):
    hospitals = {h.cms_provider_id:h for h in db.query(Hospital).options(selectinload(Hospital.location),selectinload(Hospital.quality),selectinload(Hospital.specialties)).all()}
    specialties = {s.name:s for s in db.query(Specialty).all()}
    entries = {(e.hospital_id,e.kind,e.name):e for e in db.query(DirectoryEntry).all()}
    seen = set()
    for row in rows:
        fid = row['Facility ID'].strip()
        if not fid or fid in seen: raise ValueError('Missing or duplicate CMS facility ID.')
        seen.add(fid)
        h = hospitals.get(fid)
        if h is None:
            h=Hospital(id=str(uuid.uuid4()),cms_provider_id=fid,name=row['Facility Name']); db.add(h)
            # DirectoryEntry has no ORM relationship: persist its parent first.
            db.flush([h])
        h.name=row['Facility Name']; h.hospital_type=row.get('Hospital Type'); h.ownership_type=row.get('Hospital Ownership')
        h.emergency_services=row.get('Emergency Services')=='Yes'
        if h.location is None: h.location=Location(id=str(uuid.uuid4()))
        loc=h.location
        address=(row.get('Address'),row.get('City/Town'),row.get('State'),row.get('ZIP Code'))
        if (loc.address_line1,loc.city,loc.state,loc.zip_code) != address:
            loc.latitude=loc.longitude=None
        loc.address_line1,loc.city,loc.state,loc.zip_code=address
        if h.quality is None: h.quality=HospitalQuality(id=str(uuid.uuid4()))
        h.quality.cms_overall_rating=number(row.get('Hospital overall rating'))
        for field,label in [('mortality','MORT'),('safety','Safety'),('readmission','READM')]:
            for suffix,column in [('group_measure_count',f'{label} Group Measure Count'),('facility_measure_count',f'Count of Facility {label} Measures'),('better',f'Count of {label} Measures Better'),('no_different',f'Count of {label} Measures No Different'),('worse',f'Count of {label} Measures Worse')]:
                setattr(h.quality,f'{field}_{suffix}',number(row.get(column)))
        name=TYPE_SPECIALTIES.get(h.hospital_type)
        for key, old in list(entries.items()):
            if old.hospital_id == h.id and old.kind == 'specialty' and old.source_label == 'CMS hospital type' and old.name != name:
                item=specialties.get(old.name)
                if item in h.specialties: h.specialties.remove(item)
                db.delete(old); del entries[key]
        if name:
            if name not in specialties:
                specialties[name]=Specialty(id=str(uuid.uuid4()),name=name); db.add(specialties[name])
            if specialties[name] not in h.specialties: h.specialties.append(specialties[name])
            entry=entries.get((h.id,'specialty',name))
            if entry is None:
                entry=DirectoryEntry(hospital_id=h.id,kind='specialty',name=name); db.add(entry)
            if entry.source_label in (None, 'CMS hospital type'):
                entry.source_label='CMS hospital type'; entry.source_url=source_url('general'); entry.verified_on=date.today().isoformat(); entry.expires_on=None
    return len(seen)

def import_measures(db, rows, key):
    hospital_ids = dict(db.query(Hospital.cms_provider_id, Hospital.id).all())
    records={}
    for row in rows:
        hid=hospital_ids.get(row['Facility ID'].strip())
        if not hid: continue
        record=measure_record(row,key,hid)
        if record: records[(hid,record['measure_id'])]=record
    db.query(HospitalMeasure).filter_by(source_key=key).delete(synchronize_session=False)
    values=list(records.values())
    for i in range(0,len(values),2000): db.bulk_insert_mappings(HospitalMeasure,values[i:i+2000])
    if key=='experience':
        existing={o.hospital_id:o for o in db.query(PatientExperience).all()}
        for obj in existing.values():
            for field in HC_FIELDS.values(): setattr(obj,field,None)
        for rec in values:
            field=HC_FIELDS.get(rec['measure_id'])
            if not field: continue
            hid=rec['hospital_id']
            if hid not in existing:
                existing[hid]=PatientExperience(hospital_id=hid); db.add(existing[hid])
            setattr(existing[hid],field,rec['value'])
    elif key in {'outcomes','readmissions'}:
        mapping={'Hybrid_HWM':'mortality_rate','COMP_HIP_KNEE':'complication_rate'} if key=='outcomes' else {'Hybrid_HWR':'readmission_rate','READM_30_HOSP_WIDE':'readmission_rate'}
        existing={o.hospital_id:o for o in db.query(HospitalOutcomes).all()}
        for obj in existing.values():
            for field in set(mapping.values()): setattr(obj,field,None)
        for rec in values:
            field=mapping.get(rec['measure_id'])
            if not field: continue
            hid=rec['hospital_id']
            if hid not in existing:
                existing[hid]=HospitalOutcomes(hospital_id=hid); db.add(existing[hid])
            setattr(existing[hid],field,rec['value'])
    elif key=='timely':
        existing={o.hospital_id:o for o in db.query(WaitTimeEstimate).all()}
        for obj in existing.values(): obj.er_wait_minutes=None
        for rec in values:
            if rec['measure_id']!='OP_18b': continue
            hid=rec['hospital_id']
            if hid not in existing:
                existing[hid]=WaitTimeEstimate(hospital_id=hid); db.add(existing[hid])
            existing[hid].er_wait_minutes=round(rec['value'])
            existing[hid].last_updated=datetime.utcnow()
    return len(values)

def import_coordinates(db, rows):
    locations={fid:loc for fid,loc in db.query(Hospital.cms_provider_id,Location).join(Location).all()}
    count=0
    for row in rows:
        loc=locations.get(row['facility_id'].strip())
        lat,lon=number(row.get('latitude')),number(row.get('longitude'))
        address_matches = loc and all(row.get(col, '') == (getattr(loc, field) or '') for col,field in [('address','address_line1'),('city','city'),('state','state'),('zip_code','zip_code')])
        if address_matches and lat is not None and lon is not None and -90<=lat<=90 and -180<=lon<=180:
            loc.latitude,loc.longitude=lat,lon; count+=1
    return count

def update_presence(db, rows, path):
    """Absence is meaningful only for a complete, unchanged official snapshot."""
    meta_path = path.with_suffix('.metadata.json')
    if not meta_path.exists(): return
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if meta.get('sha256') != checksum or meta.get('dataset_id') != SOURCES['general'][2]:
        raise ValueError('CMS snapshot provenance does not match the directory file.')
    # A truncated or regional directory must never mark the national remainder absent.
    if len(rows) < 4000 or len({r.get('State') for r in rows}) < 50:
        raise ValueError('CMS directory is unexpectedly small; absence flags were not updated.')
    seen = {r['Facility ID'].strip() for r in rows}
    db.flush()
    old = {p.hospital_id:p for p in db.query(HospitalPresence).all()}
    for hid, fid in db.query(Hospital.id, Hospital.cms_provider_id).all():
        item = old.get(hid)
        if item is None:
            item = HospitalPresence(hospital_id=hid); db.add(item)
        item.present = fid in seen
        item.checked_on = meta['downloaded_on']
        item.release_date = str(meta.get('release_date') or '') or None
        item.checksum = checksum

def import_source(key, folder=DATA_DIR, download=False):
    title,filename,_=SOURCES[key]
    with SessionLocal() as db:
        run=ImportRun(source_key=key,status='running',source_url=source_url(key)); db.add(run); db.commit(); run_id=run.id
        try:
            if download: download_source(key,folder)
            path=folder/filename
            required={'facility_id','latitude','longitude','address','city','state','zip_code'} if key=='coordinates' else {'Facility ID'}
            if key=='general': required|={'Facility Name','Address','City/Town','State','ZIP Code','Hospital Type'}
            elif key=='experience': required|={'HCAHPS Measure ID','HCAHPS Answer Percent'}
            elif key!='coordinates': required|={'Measure ID','Score'}
            rows=read_rows(path,required)
            count=import_general(db,rows) if key=='general' else import_coordinates(db,rows) if key=='coordinates' else import_measures(db,rows,key)
            if key == 'general': update_presence(db, rows, path)
            run.row_count=count; run.status='success'; run.finished_at=datetime.utcnow()
            run.checksum=hashlib.sha256(path.read_bytes()).hexdigest()
            run.message=f'{count:,} records imported from {filename}.'
            db.commit()
        except Exception as exc:
            db.rollback(); run=db.get(ImportRun,run_id)
            run.status='failed'; run.finished_at=datetime.utcnow()
            # No connection strings or raw database errors in the UI.
            run.message=f'{title}: {str(exc)[:220]}' if isinstance(exc,(ValueError,FileNotFoundError,httpx.HTTPError)) else f'{title}: import failed ({type(exc).__name__}); previous data preserved.'
            db.commit()
        return run.status

def refresh_all(download=False, geocode=False):
    """Each source commits independently; a failed source keeps its previous data."""
    with engine.connect() as lock_conn:
        locked=lock_conn.execute(text('SELECT pg_try_advisory_lock(947103)')).scalar() if engine.dialect.name=='postgresql' else True
        if not locked: raise RuntimeError('Another refresh is already running.')
        try:
            from app.services.backup_service import create_backup
            create_backup('before refresh')
            for key in SOURCES:
                if key=='coordinates' and geocode:
                    from scripts.geocode_hospitals import geocode_hospitals
                    try:
                        geocode_hospitals()
                    except Exception as exc:
                        with SessionLocal() as db:
                            db.add(ImportRun(source_key='coordinates',status='failed',finished_at=datetime.utcnow(),message=f'Census geocoding failed ({type(exc).__name__}); existing coordinates retained.')); db.commit()
                        continue
                import_source(key,download=download and key!='coordinates')
        finally:
            if engine.dialect.name=='postgresql': lock_conn.execute(text('SELECT pg_advisory_unlock(947103)'))

def current_status(db):
    sources=[]
    for key,(title,filename,_) in SOURCES.items():
        latest=db.query(ImportRun).filter_by(source_key=key).order_by(ImportRun.started_at.desc()).first()
        good=db.query(ImportRun).filter_by(source_key=key,status='success').order_by(ImportRun.finished_at.desc()).first()
        sources.append(dict(key=key,title=title,file_present=(DATA_DIR/filename).exists(),source_url=source_url(key),status=latest.status if latest else 'not_imported',rows=good.row_count if good else 0,last_success=(good.finished_at.isoformat()+'Z') if good else None,refresh_due=not good or (datetime.utcnow()-good.finished_at).days>180,message=latest.message if latest else None))
    counts={name:db.query(model).count() for name,model in [('hospitals',Hospital),('measures',HospitalMeasure),('experience',PatientExperience),('directory_entries',DirectoryEntry)]}
    counts['coordinates']=db.query(Location).filter(Location.latitude.isnot(None),Location.longitude.isnot(None)).count()
    counts['insurance_hospitals']=db.query(DirectoryEntry.hospital_id).filter(DirectoryEntry.kind=='insurance', (DirectoryEntry.expires_on.is_(None)) | (DirectoryEntry.expires_on>=date.today().isoformat())).distinct().count()
    counts['absent_from_latest_cms']=db.query(HospitalPresence).filter_by(present=False).count()
    return dict(sources=sources,counts=counts)

def import_directory(db, records):
    """Validate every submitted record before modifying directory memberships."""
    hospitals={h.cms_provider_id:h for h in db.query(Hospital).all()}
    for rec in records:
        if rec.facility_id not in hospitals: raise ValueError(f'Unknown facility ID: {rec.facility_id}')
    existing={(e.hospital_id,e.kind,e.name):e for e in db.query(DirectoryEntry).all()}
    specialties={s.name:s for s in db.query(Specialty).all()}; insurers={i.name:i for i in db.query(Insurance).all()}
    for rec in records:
        h=hospitals[rec.facility_id]; key=(h.id,rec.kind,rec.name)
        entry=existing.get(key)
        if entry is None:
            entry=DirectoryEntry(hospital_id=h.id,kind=rec.kind,name=rec.name); existing[key]=entry; db.add(entry)
        entry.source_url=str(rec.source_url); entry.source_label=rec.source_label
        entry.verified_on=rec.verified_on.isoformat(); entry.expires_on=rec.expires_on.isoformat() if rec.expires_on else None
        collection,model,relation=(specialties,Specialty,h.specialties) if rec.kind=='specialty' else (insurers,Insurance,h.insurance_plans)
        if rec.name not in collection:
            collection[rec.name]=model(id=str(uuid.uuid4()),name=rec.name); db.add(collection[rec.name])
        item=collection[rec.name]
        if rec.expires_on and rec.expires_on<date.today():
            if item in relation: relation.remove(item)
        elif item not in relation: relation.append(item)
    db.commit()
    return len(records)
