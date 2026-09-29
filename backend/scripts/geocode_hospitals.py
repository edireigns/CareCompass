"""Geocode missing public hospital addresses with Census and cache matched inputs."""
import csv
import io
import math
import re
from datetime import date
import httpx
from sqlalchemy import or_
from app.db.session import SessionLocal
from app.models.hospital import Hospital, Location

def parse_coordinates(value):
    try:
        lon,lat=map(float,value.split(','))
        return (lat,lon) if math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180 else None
    except (ValueError,TypeError,AttributeError): return None

def query_address(address):
    if re.match(r'^\s*P\.?\s*O\.?\s*BOX\b', address or '', flags=re.I):
        return address.strip()
    return re.sub(r'[,;]?\s+(?:P\.?\s*O\.?\s*BOX|BOX|SUITE|STE|FLOOR|FL)\s+[A-Z0-9 -]+$', '', address or '', flags=re.I).strip(' ,')

def geocode_hospitals():
    from app.services.data_service import DATA_DIR, read_rows
    path=DATA_DIR/'Hospital_Coordinates.csv'
    fields=['facility_id','latitude','longitude','source_url','matched_address','address','city','state','zip_code','query_address','verified_on','address_source_url']
    corrections_path=DATA_DIR.parent/'verified'/'address-corrections.csv'
    corrections={r['facility_id']:r for r in read_rows(corrections_path,{'facility_id','original_address','query_address','source_url'})} if corrections_path.exists() else {}
    existing={r['facility_id']:r for r in read_rows(path,{'facility_id'})} if path.exists() else {}
    with SessionLocal() as db:
        rows=db.query(Hospital.cms_provider_id,Location).join(Location).filter(or_(Location.latitude.is_(None),Location.longitude.is_(None))).all()
        with httpx.Client(timeout=360) as client:
            for start in range(0,len(rows),1000):
                group=rows[start:start+1000]; inputs={fid:loc for fid,loc in group}
                content=io.StringIO(); writer=csv.writer(content); queries={}
                for fid,loc in group:
                    correction=corrections.get(fid,{})
                    verified=correction.get('original_address')==loc.address_line1 and all(correction.get(k)==getattr(loc,k) for k in ('city','state','zip_code'))
                    address=correction['query_address'] if verified else query_address(loc.address_line1)
                    queries[fid]=(address,correction.get('source_url','') if verified else '')
                    writer.writerow([fid,address,loc.city or '',loc.state or '',loc.zip_code or ''])
                response=client.post('https://geocoding.geo.census.gov/geocoder/locations/addressbatch',data={'benchmark':'Public_AR_Current'},files={'addressFile':('hospitals.csv',content.getvalue(),'text/csv')})
                response.raise_for_status()
                for row in csv.reader(io.StringIO(response.text)):
                    if len(row)<6 or row[2].lower()!='match' or row[0] not in inputs: continue
                    point=parse_coordinates(row[5])
                    if point is None: continue
                    lat,lon=point; loc=inputs[row[0]]
                    existing[row[0]]=dict(facility_id=row[0],latitude=lat,longitude=lon,source_url='https://geocoding.geo.census.gov/',matched_address=row[4],address=loc.address_line1,city=loc.city,state=loc.state,zip_code=loc.zip_code,query_address=queries[row[0]][0],verified_on=date.today().isoformat(),address_source_url=queries[row[0]][1])
                temporary=path.with_suffix('.tmp')
                with temporary.open('w',encoding='utf-8',newline='') as handle:
                    output=csv.DictWriter(handle,fieldnames=fields); output.writeheader(); output.writerows(existing.values())
                temporary.replace(path)
        unresolved=[dict(facility_id=fid,name='',address=loc.address_line1,city=loc.city,state=loc.state,zip_code=loc.zip_code) for fid,loc in rows if fid not in existing or existing[fid]['address'] != loc.address_line1]
        with (DATA_DIR/'Unmatched_Address_Review.csv').open('w',encoding='utf-8',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=['facility_id','name','address','city','state','zip_code'])
            writer.writeheader(); writer.writerows(unresolved)
    return len(existing)

if __name__=='__main__':
    from app.services.data_service import import_source
    print('Cached coordinates:',geocode_hospitals())
    print('Import:',import_source('coordinates'))
