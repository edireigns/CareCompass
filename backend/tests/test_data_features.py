"""Data semantics, rollback, verified directories and ranking/nearby API regressions.

Uses an isolated SQLite database. Never connects to the configured project database.
"""
import os
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
from datetime import date, timedelta
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db.session import Base
from app.models.hospital import Hospital, Location, HospitalQuality, WaitTimeEstimate, PatientExperience
from app.models.data import HospitalMeasure, DirectoryEntry, ImportRun
from app.services import data_service as ds
from app.api.routes.data import DirectoryRecord
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.main import app
from app.api.deps import get_db

@pytest.fixture
def db():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    with factory() as session:
        with patch.object(ds, 'SessionLocal', factory):
            yield session
    engine.dispose()

def hospital(db, fid='000001', rating=5, duration=550, lat=41.88, lon=-87.63):
    h=Hospital(cms_provider_id=fid, name='Test '+fid, location=Location(address_line1='1 MAIN ST',city='CHICAGO',state='IL',zip_code='60601',latitude=lat,longitude=lon), quality=HospitalQuality(cms_overall_rating=rating), wait_time=WaitTimeEstimate(er_wait_minutes=duration))
    db.add(h); db.commit(); return h

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with patch('app.api.routes.data.create_backup', return_value={'name':'test.dump'}), TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def record(**values):
    return DirectoryRecord(**dict(facility_id='000001',kind='insurance',name='Test Plan',source_url='https://example.org/directory',source_label='Test verified directory',verified_on=date.today()-timedelta(days=2),**values))

def test_numeric_zero_suppression_and_units():
    assert ds.number('0') == 0
    for v in ('Not Available','Not Applicable','NaN','inf',None): assert ds.number(v) is None
    assert ds.measure_record({'Measure ID':'HAI_1_SIR','Score':'0'},'infections','h')['unit'] == 'observed / expected ratio'
    assert ds.measure_record({'Measure ID':'PSI_90','Score':'0.8'},'outcomes','h')['unit'] == 'composite index'
    assert ds.measure_record({'Measure ID':'COMP_HIP_KNEE','Score':'3.1'},'outcomes','h')['unit'] == '%'
    assert ds.measure_record({'Measure ID':'READM_30_HF','Score':'999'},'readmissions','h') is None

def test_repeatable_measures_clear_suppressed_preserve_zero(db):
    h=hospital(db)
    rows=[{'Facility ID':'000001','HCAHPS Measure ID':'H_HSP_RATING_9_10','HCAHPS Answer Percent':'0'}]
    for _ in range(2): ds.import_measures(db,rows,'experience'); db.commit()
    assert db.query(HospitalMeasure).count()==1
    assert db.query(PatientExperience).one().overall_satisfaction==0
    rows[0]['HCAHPS Answer Percent']='Not Available'
    ds.import_measures(db,rows,'experience'); db.commit()
    assert db.query(HospitalMeasure).count()==0
    assert db.query(PatientExperience).one().overall_satisfaction is None

def test_import_failure_rolls_back_previous_source(db,tmp_path):
    h=hospital(db)
    db.add(HospitalMeasure(hospital_id=h.id,source_key='outcomes',measure_id='COMP_HIP_KNEE',name='Complications',value=3,unit='%',source_url='https://example.org')); db.commit()
    (tmp_path/ds.SOURCES['outcomes'][1]).write_text('Facility ID,Wrong\n000001,anything\n')
    assert ds.import_source('outcomes',tmp_path)=='failed'
    assert db.query(HospitalMeasure).one().value==3
    assert db.query(ImportRun).one().status=='failed'

def test_coordinate_import_requires_same_address_and_valid_bounds(db):
    h=hospital(db,lat=None,lon=None)
    row=dict(facility_id='000001',latitude='41.88',longitude='-87.63',address='1 MAIN ST',city='CHICAGO',state='IL',zip_code='60601')
    assert ds.import_coordinates(db,[dict(row,address='OLD ADDRESS'),dict(row,latitude='999')])==0
    assert ds.import_coordinates(db,[row])==1
    assert h.location.latitude==41.88

def test_directory_idempotence_expiry_and_detail_serialization(db):
    h=hospital(db)
    for _ in range(2): ds.import_directory(db,[record()])
    repo=HospitalRepository(db); service=HospitalService(repo)
    assert repo.list_insurance()==['Test Plan']
    assert len(repo.search(insurance='Test Plan'))==1
    assert service.get_detail(h.id).insurance_plans==['Test Plan']
    assert db.query(DirectoryEntry).count()==1
    ds.import_directory(db,[record(expires_on=date.today()-timedelta(days=1))])
    assert repo.list_insurance()==[]
    assert repo.search(insurance='Test Plan')==[]
    detail=service.get_detail(h.id)
    assert detail.insurance_plans==[] and len(detail.directory_entries)==1

def test_unknown_facility_rejects_whole_directory_import(db):
    hospital(db)
    bad=record().model_copy(update={'facility_id':'missing'})
    with pytest.raises(ValueError): ds.import_directory(db,[record(),bad])
    assert db.query(DirectoryEntry).count()==0

def test_general_import_preserves_identity_and_removes_old_type_specialty(db):
    h=hospital(db)
    row={'Facility ID':'000001','Facility Name':'Renamed','Hospital Type':'Psychiatric','Address':'1 MAIN ST','City/Town':'CHICAGO','State':'IL','ZIP Code':'60601'}
    for _ in range(2): ds.import_general(db,[row]); db.commit()
    assert db.query(Hospital).one().id==h.id
    assert HospitalRepository(db).list_specialties()==['Mental and behavioral health']
    row['Hospital Type']='Acute Care Hospitals'
    ds.import_general(db,[row]); db.commit()
    assert HospitalRepository(db).list_specialties()==[]
    assert db.query(Hospital).one().location.latitude==41.88

def test_rankings_weights_change_results_and_validate(client,db):
    high=hospital(db,'000001',rating=5,duration=550)
    fast=hospital(db,'000002',rating=2,duration=20)
    base=dict(quality=0,wait_time=0,distance=0,satisfaction=0,readmission=0)
    assert client.get('/api/v1/rankings',params=dict(base,quality=1)).json()[0]['id']==high.id
    assert client.get('/api/v1/rankings',params=dict(base,wait_time=1)).json()[0]['id']==fast.id
    for params in (base,dict(base,quality=-1),dict(base,quality=1,lat=41)):
        assert client.get('/api/v1/rankings',params=params).status_code==422

def test_nearby_does_not_truncate_at_100_and_zero_is_first(db):
    for n in range(105): hospital(db,f'{n:06}',lat=41.88+n*.001)
    results=HospitalService(HospitalRepository(db)).nearby(41.88,-87.63,25)
    assert len(results)==105 and results[0].distance_miles==0

def test_admin_requires_local_origin_header_and_valid_records(client,db):
    hospital(db)
    payload={'records':[record().model_dump(mode='json')]}
    assert client.post('/api/v1/data/directory',json=payload).status_code==403
    headers={'X-CareCompass-Admin':'1','Origin':'https://untrusted.example'}
    assert client.post('/api/v1/data/directory',json=payload,headers=headers).status_code==403
    headers={'X-CareCompass-Admin':'1'}
    assert client.post('/api/v1/data/directory',json=payload,headers=headers).status_code==200
    payload['records'][0]['verified_on']=(date.today()+timedelta(days=1)).isoformat()
    assert client.post('/api/v1/data/directory',json=payload,headers=headers).status_code==422
    ds.refresh_lock.acquire()
    try: assert client.post('/api/v1/data/refresh',json={},headers=headers).status_code==409
    finally: ds.refresh_lock.release()

def test_weighted_coverage_excludes_missing_and_handles_zero(db):
    from app.services.ranking_service import explain_score
    from app.schemas.hospital import RankingWeights
    h=hospital(db,rating=5,duration=0)
    weights=RankingWeights(quality=.2,wait_time=.3,distance=0,satisfaction=.5,readmission=0)
    info=explain_score(h,weights)
    assert info['coverage_pct']==50 and info['sufficient_data']
    assert info['overall_score']==100
    assert sum(c['effective_weight'] for c in info['components'])==pytest.approx(1)
    assert sum(c['contribution'] or 0 for c in info['components'])==pytest.approx(100)
    assert next(c for c in info['components'] if c['key']=='satisfaction')['contribution'] is None

def test_low_coverage_follows_supported_score(db):
    from app.schemas.hospital import RankingWeights
    high=hospital(db,'000001',rating=5)
    high.wait_time.er_wait_minutes=None
    supported=hospital(db,'000002',rating=2,duration=500)
    db.commit()
    weights=RankingWeights(quality=.2,wait_time=.8,distance=0,satisfaction=0,readmission=0)
    ranked=HospitalService(HospitalRepository(db)).rankings(10,weights)
    assert [h.id for h in ranked]==[supported.id,high.id]
    assert ranked[1].overall_score==100 and ranked[1].score_explanation.coverage_pct==20

def test_same_preferences_produce_identical_scores_in_every_view(client,db):
    a=hospital(db,'000001'); b=hospital(db,'000002')
    params=dict(quality=.2,wait_time=.3,distance=.4,satisfaction=.1,readmission=0,lat=41.9,lon=-87.6)
    search=client.get('/api/v1/search',params=dict(params,city='CHICAGO')).json()
    ranked=client.get('/api/v1/rankings',params=params).json()
    nearby=client.get('/api/v1/nearby',params=params).json()
    detail=client.get('/api/v1/hospital/'+a.id,params=params).json()
    compared=client.get('/api/v1/compare',params={**params,'ids':[b.id,a.id]}).json()
    assert [h['id'] for h in compared]==[b.id,a.id]
    for response in (search,ranked,nearby,compared):
        row=next(h for h in response if h['id']==a.id)
        assert row['overall_score']==detail['overall_score']
        assert row['score_explanation']==detail['score_explanation']
        assert row['distance_miles']==detail['distance_miles']

def test_invalid_preferences_rejected_across_views(client,db):
    a=hospital(db); b=hospital(db,'000002')
    for path in ('/search','/rankings','/nearby','/hospital/'+a.id,'/compare'):
        result=client.get('/api/v1'+path,params={'quality':-1,'lat':41,'lon':-87,'ids':[a.id,b.id]})
        assert result.status_code==422
