from types import SimpleNamespace as NS
from datetime import date
from app.schemas.hospital import ScoreExplanation, RankingWeights
from app.services.evidence_scoring import explain_score
from app.services.score_dates import attach_score_dates
from app.services.directory_taxonomy import specialty_category, insurance_carrier
from app.repositories.hospital_repository import HospitalRepository
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base
from app.models.hospital import Hospital, Location, HospitalQuality, WaitTimeEstimate

@pytest.fixture
def db():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, autoflush=False)() as session:
        yield session
    engine.dispose()

def hospital(db, fid='000001'):
    h=Hospital(cms_provider_id=fid, name='Test '+fid, location=Location(address_line1='1 MAIN ST',city='CHICAGO',state='IL',zip_code='60601',latitude=41.88,longitude=-87.63), quality=HospitalQuality(cms_overall_rating=5), wait_time=WaitTimeEstimate(er_wait_minutes=200))
    db.add(h); db.commit(); return h
from app.services.data_service import import_directory

def evidence(mid,value,end):
    return NS(measure_id=mid,value=value,period_start='01/01/2019',period_end=end,source_url='https://data.cms.gov/')

def score(weights):
    h=NS(quality=NS(cms_overall_rating=5),wait_time=NS(er_wait_minutes=200),experience=NS(overall_satisfaction=80),outcomes=NS(readmission_rate=10))
    return ScoreExplanation(**explain_score(h,weights))

def test_only_selected_contributing_measure_dates_are_counted():
    info=score(RankingWeights(quality=0,wait_time=1,distance=0,satisfaction=0,readmission=0))
    result=attach_score_dates(info,[evidence('OP_18b',200,'12/31/2020'),evidence('H_HSP_RATING_9_10',80,'12/31/2019')])
    assert result['older_measure_count']==1
    assert result['oldest_period_end']=='2020-12-31'
    assert result['unknown_period_count']==0
    assert info.components[1].measure_id=='OP_18b'
    assert info.components[3].date_status=='not_used'

def test_quality_release_is_not_a_clinical_reporting_period():
    info=score(RankingWeights(quality=1,wait_time=0,distance=0,satisfaction=0,readmission=0))
    result=attach_score_dates(info,[],NS(present=True,release_date='2026-07-22'))
    assert result['unknown_period_count']==1
    assert result['oldest_period_end'] is None
    assert info.components[0].release_date=='2026-07-22'
    assert info.components[0].date_status=='release_only'

def test_ambiguous_or_mismatched_summary_dates_stay_unknown():
    info=score(RankingWeights(quality=0,wait_time=0,distance=0,satisfaction=0,readmission=1))
    result=attach_score_dates(info,[evidence('Hybrid_HWR',10,'12/31/2020'),evidence('READM_30_HOSP_WIDE',10,'12/31/2021')])
    assert result['unknown_period_count']==1
    assert info.components[-1].period_end is None
    assert info.overall_score==60

def test_specialty_aliases_expand_without_renaming_evidence(db):
    a=hospital(db); b=hospital(db,'000002')
    from app.api.routes.data import DirectoryRecord
    entries=[DirectoryRecord(facility_id=fid,kind='specialty',name=name,source_url='https://example.org/',source_label='Verified services',verified_on=date.today()) for fid,name in [('000001','Orthopaedics'),('000002','Orthopedics')]]
    import_directory(db,entries)
    repo=HospitalRepository(db)
    assert repo.list_specialties()==['Orthopedics']
    assert len(repo.search(specialty='Orthopedics'))==2
    from app.models.data import DirectoryEntry
    assert {e.name for e in db.query(DirectoryEntry)}=={'Orthopaedics','Orthopedics'}

def test_carrier_does_not_merge_network_tier_or_year(db):
    hospital(db); hospital(db,'000002')
    from app.api.routes.data import DirectoryRecord
    names=['2026 Blue Cross Blue Shield - Blue Choice Options (Tier 1)','2026 Blue Cross Blue Shield - Blue Choice Options (Tier 2)']
    import_directory(db,[DirectoryRecord(facility_id=fid,kind='insurance',name=name,source_url='https://example.org/',source_label='Verified plans',verified_on=date.today()) for fid,name in zip(['000001','000002'],names)])
    repo=HospitalRepository(db)
    assert len(repo.search(carrier='Blue Cross Blue Shield'))==2
    assert len(repo.search(carrier='Blue Cross Blue Shield',insurance=names[0]))==1
    assert repo.search(insurance=names[0].replace('2026','2025'))==[]
    assert len(repo.list_insurance())==2
    assert insurance_carrier('UNITED HEALTH CARE - OPTIONS PPO')=='UnitedHealthcare'

def test_chicago_coverage_excludes_other_cities_absent_and_expired(db):
    from app.models.data import HospitalPresence, DirectoryEntry
    from app.services.coverage_service import chicago_coverage
    a=hospital(db); b=hospital(db,'000002'); c=hospital(db,'000003')
    b.location.city='NORTH CHICAGO'
    for h,present in [(a,True),(b,True),(c,False)]:
        db.add(HospitalPresence(hospital_id=h.id,present=present,checked_on='2026-09-29',checksum='test'))
    for kind,name,label,expires in [('specialty','Acute Care','CMS hospital type',None),('insurance','Old Plan','Official','2000-01-01'),('specialty','Cardiology','Hospital services',None)]:
        db.add(DirectoryEntry(hospital_id=a.id,kind=kind,name=name,source_url='https://example.org',source_label=label,verified_on='2000-01-01',expires_on=expires))
    db.commit()
    result=chicago_coverage(db)
    assert result['total']==1
    assert result['coordinates']==1
    assert result['insurance_hospitals']==0
    assert result['clinical_specialty_records']==1

def test_same_scoring_evidence_dates_across_views(db):
    from app.services.hospital_service import HospitalService
    from app.models.data import HospitalMeasure
    h=hospital(db)
    db.add(HospitalMeasure(hospital_id=h.id,source_key='timely',measure_id='OP_18b',name='Wait',value=200,unit='minutes',period_start='01/01/2019',period_end='12/31/2020',source_url='https://data.cms.gov'))
    db.commit()
    service=HospitalService(HospitalRepository(db))
    weights=RankingWeights(quality=0,wait_time=1,distance=0,satisfaction=0,readmission=0)
    views=[service.search(weights=weights)[0],service.rankings(weights=weights)[0],service.get_detail(h.id,weights),service.compare([h.id],weights)[0],service.nearby(41.88,-87.63,weights=weights)[0]]
    assert len({v.overall_score for v in views})==1
    assert all(v.score_freshness.older_measure_count==1 for v in views)
    assert all(v.score_explanation.components[1].period_end=='12/31/2020' for v in views)
