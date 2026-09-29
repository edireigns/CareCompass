"""Review actions and backup safeguards on isolated temporary storage."""
import csv
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.session import Base
from app.models.hospital import Hospital, Location
from app.models.data import DirectoryEntry, HospitalPresence, ReviewEvent
from app.services import review_service as review, backup_service as backups

@pytest.fixture
def db():
    engine=create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as session: yield session
    engine.dispose()

def seed(db):
    h=Hospital(cms_provider_id='000099',name='Review Hospital',location=Location(address_line1='1 MAIN ST',city='CHICAGO',state='IL',zip_code='60601'),
        cms_presence=HospitalPresence(present=True,checksum='release-a',checked_on='2026-09-29',release_date='2026-09-29'))
    db.add(h);db.commit()
    return h

def test_review_queue_correction_and_history(db,tmp_path,monkeypatch):
    h=seed(db)
    csv_path=tmp_path/'Hospital_Coordinates.csv'
    fields=['facility_id','latitude','longitude','source_url','matched_address','address','city','state','zip_code','query_address','verified_on','address_source_url']
    with csv_path.open('w',newline='') as handle: csv.DictWriter(handle,fieldnames=fields).writeheader()
    monkeypatch.setattr(review,'COORDINATES',csv_path)
    item=review.queue(db)['items'][0]
    assert item['kind']=='address' and item['facility_id']=='000099'
    review.record_review(db,item['issue_id'],'reviewed','Checked CMS address','https://data.cms.gov')
    assert review.queue(db)['counts']['address']==0
    assert review.queue(db,show_reviewed=True)['items'][0]['reviewed']
    with patch.object(backups,'create_backup',return_value={'name':'before.dump'}) as backup:
        review.record_review(db,item['issue_id'],'correct','Verified exact hospital point','https://example.org/location',41.88,-87.63)
        backup.assert_called_once()
    assert review.queue(db)['counts']['address']==0
    assert h.location.latitude==41.88
    assert len(review.history(db,'000099'))==2
    assert '000099' in csv_path.read_text()

def test_review_directory_and_absence_keep_source_history(db):
    h=seed(db)
    old=(date.today()-timedelta(days=210)).isoformat()
    entry=DirectoryEntry(hospital_id=h.id,kind='insurance',name='Exact Plan',source_url='https://example.org/old',source_label='Directory',verified_on=old)
    db.add(entry);db.commit()
    issues=review.queue(db)['items']
    assert any(i['kind']=='record' for i in issues)
    with patch.object(backups,'create_backup',return_value={'name':'before.dump'}):
        review.record_review(db,'record:'+entry.id,'confirm','Confirmed current directory entry','https://example.org/new')
    assert entry.verified_on==date.today().isoformat()
    assert not any(i['kind']=='record' for i in review.queue(db)['items'])
    h.cms_presence.present=False;db.commit()
    assert any(i['kind']=='presence' for i in review.queue(db)['items'])
    review.record_review(db,'presence:000099','reviewed','Checked newer CMS release','https://data.cms.gov')
    assert not h.cms_presence.present
    assert db.query(ReviewEvent).count()==2

def test_backup_mirror_failure_prevents_data_change(tmp_path,monkeypatch):
    monkeypatch.setattr(backups,'BACKUP_DIR',tmp_path/'local')
    monkeypatch.setattr(backups,'mirror_destination',lambda:tmp_path/'unavailable')
    def dump(_name,args):
        target=args[args.index('--file')+1]
        from pathlib import Path
        Path(target).write_bytes(b'archive')
    with patch.object(backups,'run',side_effect=dump),patch.object(backups,'validate_archive'):
        with pytest.raises(backups.BackupError,match='other drive is unavailable'):
            backups.create_backup('before import')
    assert len(list((tmp_path/'local').glob('*.dump')))==1
