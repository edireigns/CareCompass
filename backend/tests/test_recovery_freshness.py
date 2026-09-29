import hashlib
import json
from datetime import date
from unittest.mock import patch
import pytest
from app.services import backup_service as bs, data_service as ds
from app.services.freshness_service import reporting_status, directory_status
from scripts.geocode_hospitals import query_address

def test_reporting_period_and_expiry_are_distinct():
    today=date(2026,9,28)
    assert reporting_status('09/27/2024',today)=='older_period'
    assert reporting_status('09/28/2024',today)=='recent_period'
    assert reporting_status(None,today)=='unknown'
    assert reporting_status('2030-01-01',today)=='future_period'
    assert directory_status('2026-09-01','2026-09-27',today)=='expired'
    assert directory_status('2026-01-01',None,today)=='review_due'
    assert directory_status('2026-09-01','2026-09-28',today)=='recently_verified'

def test_normalize_delivery_details_without_guessing_street():
    assert query_address('225 E CHICAGO AVE, BOX 140')=='225 E CHICAGO AVE'
    assert query_address('123 MAIN ST SUITE 2')=='123 MAIN ST'
    assert query_address('PO BOX 90')=='PO BOX 90'
    assert query_address('100 HIGHWAY 20')=='100 HIGHWAY 20'

def test_restore_requires_confirmation_and_confines_path(tmp_path,monkeypatch):
    monkeypatch.setattr(bs,'BACKUP_DIR',tmp_path)
    with patch.object(bs,'run') as run:
        with pytest.raises(bs.BackupError): bs.restore_backup('x.dump','')
        with pytest.raises(bs.BackupError): bs.restore_backup('../x.dump','RESTORE')
        run.assert_not_called()

def test_tampered_archive_never_restored(tmp_path,monkeypatch):
    monkeypatch.setattr(bs,'BACKUP_DIR',tmp_path)
    (tmp_path/'x.dump').write_bytes(b'tampered')
    (tmp_path/'x.json').write_text(json.dumps({'sha256':'invalid'}))
    with patch.object(bs,'run') as run:
        with pytest.raises(bs.BackupError,match='checksum'): bs.restore_backup('x.dump','RESTORE')
        run.assert_not_called()

def test_restore_backup_failure_prevents_replace(tmp_path,monkeypatch):
    monkeypatch.setattr(bs,'BACKUP_DIR',tmp_path)
    (tmp_path/'x.dump').write_bytes(b'archive')
    (tmp_path/'x.json').write_text(json.dumps({'sha256':hashlib.sha256(b'archive').hexdigest()}))
    with patch.object(bs,'validate_archive'), patch.object(bs,'create_backup',side_effect=bs.BackupError('disk full')), patch.object(bs,'run') as run:
        with pytest.raises(bs.BackupError): bs.restore_backup('x.dump','RESTORE')
        run.assert_not_called()

def test_refresh_backup_failure_prevents_import():
    from sqlalchemy import create_engine
    with patch.object(ds,'engine',create_engine('sqlite://')), patch.object(bs,'create_backup',side_effect=bs.BackupError('disk full')), patch.object(ds,'import_source') as importer:
        with pytest.raises(bs.BackupError): ds.refresh_all()
        importer.assert_not_called()

def test_partial_or_modified_snapshot_cannot_mark_absent(tmp_path):
    path=tmp_path/'directory.csv';path.write_text('small dataset')
    meta={'dataset_id':ds.SOURCES['general'][2],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    path.with_suffix('.metadata.json').write_text(json.dumps(meta))
    with pytest.raises(ValueError,match='unexpectedly small'): ds.update_presence(None,[],path)
    path.write_text('changed')
    with pytest.raises(ValueError,match='provenance'): ds.update_presence(None,[],path)

def test_new_hospital_directory_evidence_respects_foreign_keys():
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session
    from app.db.session import Base
    from app.models.data import DirectoryEntry
    engine=create_engine('sqlite://')
    @event.listens_for(engine,'connect')
    def foreign_keys(connection, _): connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine,autoflush=False) as db:
        ds.import_general(db,[{'Facility ID':'000099','Facility Name':'New hospital','Hospital Type':'Psychiatric'}])
        db.commit()
        assert db.query(DirectoryEntry).one().name=='Psychiatry'
    engine.dispose()
