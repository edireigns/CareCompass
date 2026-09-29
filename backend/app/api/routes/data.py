"""Local administration: refresh public source data and import verified directory records."""
from datetime import date, datetime
from typing import Literal
from urllib.parse import urlsplit
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl, model_validator
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.data import ImportRun
from app.services import data_service
from app.services.backup_service import create_backup, list_backups, BackupError

router=APIRouter(prefix='/data',tags=['data'])

def require_local_admin(request: Request):
    client=request.client.host if request.client else ''
    host=urlsplit('http://'+request.headers.get('host','')).hostname
    origin=request.headers.get('origin')
    if client not in {'127.0.0.1','::1','testclient'} or host not in {'localhost','127.0.0.1','::1','testserver'}:
        raise HTTPException(403,'Data changes are available only on this computer.')
    if request.headers.get('x-carecompass-admin')!='1' or (origin and origin not in get_settings().cors_origin_list):
        raise HTTPException(403,'Open CareCompass locally to change data.')

class RefreshRequest(BaseModel):
    download_latest: bool=False
    geocode_missing: bool=False

class DirectoryRecord(BaseModel):
    facility_id: str=Field(min_length=1,max_length=20,pattern=r'^[A-Za-z0-9]+$')
    kind: Literal['insurance','specialty']
    name: str=Field(min_length=2,max_length=200)
    source_url: HttpUrl
    source_label: str=Field(min_length=2,max_length=120)
    verified_on: date
    expires_on: date | None=None

    @model_validator(mode='after')
    def dates(self):
        self.name=self.name.strip()
        if len(self.name)<2: raise ValueError('A name is required.')
        if self.verified_on>date.today(): raise ValueError('Verification date cannot be in the future.')
        if self.expires_on and self.expires_on<self.verified_on: raise ValueError('Expiry must follow verification.')
        return self

class DirectoryRequest(BaseModel):
    records:list[DirectoryRecord]=Field(min_length=1,max_length=5000)

@router.get('/status')
def status(db:Session=Depends(get_db)):
    result=data_service.current_status(db)
    latest=db.query(ImportRun).filter_by(source_key='refresh').order_by(ImportRun.started_at.desc()).first()
    result['job']=dict(id=latest.id,status=latest.status,message=latest.message,started_at=latest.started_at.isoformat()+'Z',finished_at=latest.finished_at.isoformat()+'Z' if latest.finished_at else None) if latest else None
    result['backups']=list_backups()[:10]
    result['running']=data_service.refresh_lock.locked()
    return result

def run_refresh(job_id, payload):
    try:
        data_service.refresh_all(download=payload.download_latest,geocode=payload.geocode_missing)
        with SessionLocal() as db:
            job=db.get(ImportRun,job_id)
            failed=db.query(ImportRun).filter(ImportRun.id!=job_id,ImportRun.started_at>=job.started_at,ImportRun.status=='failed').count()
            job.status='partial_failure' if failed else 'success'
            job.message='Some sources failed. Their previous data is preserved; see source details.' if failed else 'Refresh complete.'
            job.finished_at=datetime.utcnow(); db.commit()
    except Exception as exc:
        with SessionLocal() as db:
            job=db.get(ImportRun,job_id); job.status='failed'; job.finished_at=datetime.utcnow()
            job.message=str(exc) if isinstance(exc, BackupError) else 'Refresh stopped. Check source statuses and retry; committed source imports are retained.'; db.commit()
    finally:
        data_service.refresh_lock.release()

@router.post('/refresh',status_code=202,dependencies=[Depends(require_local_admin)])
def refresh(payload:RefreshRequest, background:BackgroundTasks, db:Session=Depends(get_db)):
    if not data_service.refresh_lock.acquire(blocking=False): raise HTTPException(409,'A refresh is already running.')
    try:
        job=ImportRun(source_key='refresh',status='running',message='Importing hospital data...'); db.add(job); db.commit()
        background.add_task(run_refresh,job.id,payload)
        return {'job_id':job.id,'status':'running'}
    except Exception:
        data_service.refresh_lock.release(); raise

@router.post('/directory',dependencies=[Depends(require_local_admin)])
def directory(payload:DirectoryRequest,db:Session=Depends(get_db)):
    if not data_service.refresh_lock.acquire(blocking=False): raise HTTPException(409,'A data import is already running.')
    try:
        create_backup('before directory import')
        count=data_service.import_directory(db,payload.records)
        return {'imported':count}
    except BackupError as exc:
        raise HTTPException(503,str(exc))
    except ValueError as exc:
        db.rollback(); raise HTTPException(422,str(exc))
    finally:
        data_service.refresh_lock.release()

@router.post('/backup', dependencies=[Depends(require_local_admin)])
def backup():
    if not data_service.refresh_lock.acquire(blocking=False):
        raise HTTPException(409, 'A data operation is already running.')
    try:
        return create_backup('manual')
    except BackupError as exc:
        raise HTTPException(503, str(exc))
    finally:
        data_service.refresh_lock.release()

@router.get('/backup-destination',dependencies=[Depends(require_local_admin)])
def backup_destination():
    from app.services.backup_service import mirror_status
    try: return mirror_status()
    except BackupError as exc: raise HTTPException(503,str(exc))

class BackupDestinationRequest(BaseModel):
    destination:str|None=Field(default=None,max_length=500)

@router.post('/backup-destination',dependencies=[Depends(require_local_admin)])
def set_backup_destination(payload:BackupDestinationRequest):
    from app.services.backup_service import configure_mirror,mirror_status
    if data_service.refresh_lock.locked(): raise HTTPException(409,'A data operation is already running.')
    try:
        configure_mirror(payload.destination)
        return mirror_status()
    except BackupError as exc: raise HTTPException(422,str(exc))

@router.post('/backup/{name}/verify',dependencies=[Depends(require_local_admin)])
def verify_archive(name:str):
    from app.services.backup_service import verify_backup
    if not data_service.refresh_lock.acquire(blocking=False): raise HTTPException(409,'A data operation is already running.')
    try: return verify_backup(name)
    except BackupError as exc: raise HTTPException(422,str(exc))
    finally: data_service.refresh_lock.release()

@router.get('/coverage/chicago')
def coverage_chicago(db:Session=Depends(get_db)):
    from app.services.coverage_service import chicago_coverage
    return chicago_coverage(db)

@router.get('/review/queue',dependencies=[Depends(require_local_admin)])
def review_queue(kind:Literal['address','record','presence']|None=None,show_reviewed:bool=False,search:str='',offset:int=0,limit:int=50,db:Session=Depends(get_db)):
    from app.services.review_service import queue
    if not 0<=offset<=100000 or not 1<=limit<=100 or len(search)>120: raise HTTPException(422,'Invalid review queue page or search.')
    return queue(db,kind,show_reviewed,search,offset,limit)

@router.get('/review/history/{facility_id}',dependencies=[Depends(require_local_admin)])
def review_history(facility_id:str,db:Session=Depends(get_db)):
    from app.services.review_service import history
    return history(db,facility_id)

class ReviewRequest(BaseModel):
    issue_id:str=Field(min_length=3,max_length=100)
    action:Literal['reviewed','correct','confirm','retire']
    note:str=Field(min_length=3,max_length=1000)
    source_url:HttpUrl
    latitude:float|None=None
    longitude:float|None=None
    new_name:str|None=Field(default=None,max_length=200)
    expires_on:date|None=None

@router.post('/review',dependencies=[Depends(require_local_admin)])
def save_review(payload:ReviewRequest,db:Session=Depends(get_db)):
    from app.services.review_service import record_review
    if not data_service.refresh_lock.acquire(blocking=False): raise HTTPException(409,'A data operation is already running.')
    try:
        return record_review(db,**{**payload.model_dump(exclude={'source_url'}),'source_url':str(payload.source_url)})
    except BackupError as exc: raise HTTPException(503,str(exc))
    except ValueError as exc: db.rollback(); raise HTTPException(422,str(exc))
    finally: data_service.refresh_lock.release()
