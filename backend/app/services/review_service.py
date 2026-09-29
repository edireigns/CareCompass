"""Evidence-driven review queue; a review never changes CMS presence."""
import csv
import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import joinedload
from app.models.hospital import Hospital, Location, Specialty, Insurance
from app.models.data import DirectoryEntry, HospitalPresence, ReviewEvent
from app.services.freshness_service import directory_status

CMS_URL='https://data.cms.gov/provider-data/dataset/xubh-q36u'
COORDINATES=Path(__file__).resolve().parents[1]/'data'/'cms'/'Hospital_Coordinates.csv'

def revision(*parts):
    return hashlib.sha256(json.dumps(parts,sort_keys=True,default=str).encode()).hexdigest()

def queue(db,kind=None,show_reviewed=False,search='',offset=0,limit=50):
    hospitals=db.query(Hospital).options(joinedload(Hospital.location),joinedload(Hospital.cms_presence)).all()
    entries=db.query(DirectoryEntry).all()
    latest={}
    for event in db.query(ReviewEvent).order_by(ReviewEvent.created_at,ReviewEvent.id).all():
        latest[event.item_key]=event
    items=[]; now=datetime.utcnow()
    for h in hospitals:
        if not h.cms_provider_id: continue
        loc=h.location
        place=', '.join(x for x in [loc.city,loc.state] if x) if loc else ''
        base=dict(facility_id=h.cms_provider_id,hospital_name=h.name,place=place)
        if loc and (loc.latitude is None or loc.longitude is None) and h.cms_presence and h.cms_presence.present:
            key='address:'+h.cms_provider_id
            rev=revision(loc.address_line1,loc.city,loc.state,loc.zip_code)
            items.append(dict(base,issue_id=key,kind='address',item_key=key,source_revision=rev,source_url=CMS_URL,
                detail=f"Unmatched address: {loc.address_line1 or 'unknown'}, {place} {loc.zip_code or ''}",last_review=latest.get(key)))
        if h.cms_presence and not h.cms_presence.present:
            key='presence:'+h.cms_provider_id
            items.append(dict(base,issue_id=key,kind='presence',item_key=key,source_revision=h.cms_presence.checksum,source_url=CMS_URL,
                detail='Hospital is absent from the latest complete imported CMS directory. Review identity or closure; do not infer closure from absence alone.',last_review=latest.get(key)))
    by_id={h.id:h for h in hospitals}
    for entry in entries:
        if latest.get('record:'+entry.id) and latest['record:'+entry.id].action in {'retire','correct'}: continue
        state=directory_status(entry.verified_on,entry.expires_on)
        if state not in {'expired','review_due','unknown'}: continue
        h=by_id.get(entry.hospital_id)
        if not h: continue
        key='record:'+entry.id
        rev=revision(entry.kind,entry.name,entry.source_url,entry.verified_on,entry.expires_on)
        items.append(dict(facility_id=h.cms_provider_id,hospital_name=h.name,place=', '.join(x for x in [h.location.city,h.location.state] if x) if h.location else '',
            issue_id=key,kind='record',item_key=key,record_kind=entry.kind,record_name=entry.name,source_revision=rev,source_url=entry.source_url,
            detail=f'{state.replace("_"," ")}: {entry.name}; checked {entry.verified_on}; expires {entry.expires_on or "not specified"}',last_review=latest.get(key)))
    for item in items:
        event=item.pop('last_review')
        item['last_reviewed_at']=event.created_at.isoformat()+'Z' if event else None
        item['last_note']=event.note if event else None
        item['reviewed']=bool(event and event.source_revision==item['source_revision'] and event.action=='reviewed' and event.created_at>=now-timedelta(days=180))
    if kind: items=[i for i in items if i['kind']==kind]
    if search:
        needle=search.casefold()
        items=[i for i in items if needle in (i['hospital_name']+' '+i['facility_id']+' '+i['detail']).casefold()]
    counts={k:sum(i['kind']==k and not i['reviewed'] for i in items) for k in ('address','record','presence')}
    if not show_reviewed: items=[i for i in items if not i['reviewed']]
    items.sort(key=lambda i:(i['kind'],i['hospital_name'],i['issue_id']))
    return dict(total=len(items),counts=counts,items=items[offset:offset+limit])

def history(db,facility_id,limit=100):
    h=db.query(Hospital).filter_by(cms_provider_id=facility_id).first()
    if not h: return []
    return [dict(id=e.id,issue_type=e.issue_type,item_key=e.item_key,action=e.action,old_value=e.old_value,new_value=e.new_value,note=e.note,source_url=e.source_url,created_at=e.created_at.isoformat()+'Z') for e in db.query(ReviewEvent).filter_by(hospital_id=h.id).order_by(ReviewEvent.created_at.desc()).limit(limit)]

def record_review(db,issue_id,action,note,source_url,latitude=None,longitude=None,new_name=None,expires_on=None):
    from app.services.backup_service import create_backup
    from urllib.parse import urlsplit
    if not note.strip() or not urlsplit(source_url).scheme in {'http','https'} or not urlsplit(source_url).netloc:
        raise ValueError('Add a review note and a valid source link.')
    kind,_,identifier=issue_id.partition(':')
    if kind not in {'address','record','presence'} or not identifier: raise ValueError('Choose an item from the review queue.')
    entry=db.get(DirectoryEntry,identifier) if kind=='record' else None
    h=db.get(Hospital,entry.hospital_id) if entry else db.query(Hospital).filter_by(cms_provider_id=identifier).first()
    if not h: raise ValueError('Hospital or record no longer exists.')
    if kind=='record' and not entry: raise ValueError('Record no longer exists.')
    if action not in ({'reviewed','correct'} if kind=='address' else {'reviewed','confirm','correct','retire'} if kind=='record' else {'reviewed'}):
        raise ValueError('This action is not available for that item.')
    if kind=='address':
        loc=h.location
        if not loc or (loc.latitude is not None and loc.longitude is not None): raise ValueError('Address is already matched.')
        rev=revision(loc.address_line1,loc.city,loc.state,loc.zip_code)
        old=json.dumps(dict(address=loc.address_line1,city=loc.city,state=loc.state,zip_code=loc.zip_code,latitude=loc.latitude,longitude=loc.longitude))
        new=old
        if action=='correct':
            if latitude is None or longitude is None or not (-90<=latitude<=90 and -180<=longitude<=180): raise ValueError('Enter valid coordinates for the verified hospital location.')
            create_backup('before address correction')
            loc.latitude,loc.longitude=latitude,longitude
            new=json.dumps(dict(address=loc.address_line1,city=loc.city,state=loc.state,zip_code=loc.zip_code,latitude=latitude,longitude=longitude))
    elif kind=='record':
        rev=revision(entry.kind,entry.name,entry.source_url,entry.verified_on,entry.expires_on)
        old=json.dumps(dict(kind=entry.kind,name=entry.name,source_url=entry.source_url,verified_on=entry.verified_on,expires_on=entry.expires_on))
        new=old
        if action!='reviewed':
            create_backup('before directory correction')
            if action=='retire':
                entry.expires_on=(date.today()-timedelta(days=1)).isoformat()
                member=next((m for m in h.specialties if m.name==entry.name),None) if entry.kind=='specialty' else next((m for m in h.insurance_plans if m.name==entry.name),None)
                if member: (h.specialties if entry.kind=='specialty' else h.insurance_plans).remove(member)
            elif action=='confirm':
                entry.verified_on=date.today().isoformat(); entry.source_url=source_url
                entry.expires_on=expires_on.isoformat() if expires_on else None
                member=db.query(Specialty if entry.kind=='specialty' else Insurance).filter_by(name=entry.name).first()
                if member and member not in (h.specialties if entry.kind=='specialty' else h.insurance_plans): (h.specialties if entry.kind=='specialty' else h.insurance_plans).append(member)
            else:
                if not new_name or len(new_name.strip())<2: raise ValueError('Enter the exact replacement source name.')
                old_name=entry.name
                entry.expires_on=(date.today()-timedelta(days=1)).isoformat()
                member=next((m for m in h.specialties if m.name==old_name),None) if entry.kind=='specialty' else next((m for m in h.insurance_plans if m.name==old_name),None)
                if member: (h.specialties if entry.kind=='specialty' else h.insurance_plans).remove(member)
                replacement=db.query(DirectoryEntry).filter_by(hospital_id=h.id,kind=entry.kind,name=new_name.strip()).first()
                if replacement is None:
                    replacement=DirectoryEntry(hospital_id=h.id,kind=entry.kind,name=new_name.strip())
                    db.add(replacement)
                replacement.source_url=source_url
                replacement.source_label='Manual verified correction'
                replacement.verified_on=date.today().isoformat()
                replacement.expires_on=expires_on.isoformat() if expires_on else None
                model=Specialty if entry.kind=='specialty' else Insurance
                new_member=db.query(model).filter_by(name=new_name.strip()).first()
                if new_member is None:
                    new_member=model(name=new_name.strip()); db.add(new_member)
                relation=h.specialties if entry.kind=='specialty' else h.insurance_plans
                if new_member not in relation: relation.append(new_member)
            new=json.dumps(dict(kind=entry.kind,name=new_name.strip() if action=='correct' else entry.name,source_url=source_url,verified_on=date.today().isoformat(),expires_on=(replacement.expires_on if action=='correct' else entry.expires_on)))
    else:
        if not h.cms_presence or h.cms_presence.present: raise ValueError('Hospital is present in the latest CMS directory.')
        rev=h.cms_presence.checksum
        old=json.dumps(dict(present=False,release_date=h.cms_presence.release_date))
        new=old
    db.add(ReviewEvent(hospital_id=h.id,issue_type=kind,item_key=issue_id,action=action,source_revision=rev,old_value=old,new_value=new,note=note.strip(),source_url=source_url))
    if kind=='address' and action=='correct':
        try: cache_coordinate(h,source_url)
        except OSError as exc:
            db.rollback()
            raise ValueError('Could not save the coordinate cache; the database correction was cancelled.') from exc
    db.commit()
    return dict(status='saved',facility_id=h.cms_provider_id)

def cache_coordinate(h,source_url):
    """Keep a manual point across future CMS refreshes without changing the CMS address."""
    with COORDINATES.open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle); fields=reader.fieldnames; rows=list(reader)
    loc=h.location
    row=dict(facility_id=h.cms_provider_id,latitude=loc.latitude,longitude=loc.longitude,source_url=source_url,
        matched_address='Manual source-reviewed hospital location',address=loc.address_line1 or '',city=loc.city or '',state=loc.state or '',zip_code=loc.zip_code or '',query_address='',verified_on=date.today().isoformat(),address_source_url=source_url)
    rows=[r for r in rows if r['facility_id']!=h.cms_provider_id]+[row]
    path=COORDINATES.with_suffix('.new')
    with path.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    path.replace(COORDINATES)
