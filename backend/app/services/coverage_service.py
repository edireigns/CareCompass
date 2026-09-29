"""Coverage is evidence availability, never a claim that a hospital lacks a service."""
import json
from datetime import date
from pathlib import Path
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from app.models.hospital import Hospital, Location
from app.models.data import DirectoryEntry, HospitalPresence

REVIEWS=Path(__file__).resolve().parents[1]/'data'/'verified'/'chicago-review.json'

def chicago_coverage(db):
    hospitals=db.query(Hospital).options(joinedload(Hospital.location)).join(Location).join(HospitalPresence).filter(func.upper(Location.city)=='CHICAGO',Location.state=='IL',HospitalPresence.present.is_(True)).order_by(Hospital.name).all()
    ids=[h.id for h in hospitals]
    entries=db.query(DirectoryEntry).filter(DirectoryEntry.hospital_id.in_(ids)).all() if ids else []
    reviews=json.loads(REVIEWS.read_text(encoding='utf-8')) if REVIEWS.exists() else {}
    by_hospital={}
    for entry in entries: by_hospital.setdefault(entry.hospital_id,[]).append(entry)
    today=date.today().isoformat(); rows=[]
    for hospital in hospitals:
        active=[e for e in by_hospital.get(hospital.id,[]) if not e.expires_on or e.expires_on>=today]
        plans=[e for e in active if e.kind=='insurance']
        clinical=[e for e in active if e.kind=='specialty' and e.source_label!='CMS hospital type']
        location=hospital.location
        rows.append(dict(id=hospital.id,facility_id=hospital.cms_provider_id,name=hospital.name,coordinates=bool(location and location.latitude is not None and location.longitude is not None),insurance_records=len(plans),clinical_specialty_records=len(clinical),review=reviews.get(hospital.cms_provider_id)))
    return dict(scope='Chicago city limits, Illinois · hospitals listed in the latest imported CMS directory',total=len(rows),coordinates=sum(r['coordinates'] for r in rows),insurance_hospitals=sum(r['insurance_records']>0 for r in rows),clinical_specialty_hospitals=sum(r['clinical_specialty_records']>0 for r in rows),reviewed_hospitals=sum(bool(r['review']) for r in rows),insurance_records=sum(r['insurance_records'] for r in rows),clinical_specialty_records=sum(r['clinical_specialty_records'] for r in rows),hospitals=rows)
