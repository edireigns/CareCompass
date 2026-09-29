from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.ranking_context import RankingContext, ranking_context
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.schemas.hospital import HospitalSummary

router=APIRouter(tags=['rankings'])

@router.get('/rankings',response_model=list[HospitalSummary])
def rankings(limit:int=Query(10,ge=1,le=100),context:RankingContext=Depends(ranking_context),db:Session=Depends(get_db)):
    return HospitalService(HospitalRepository(db)).rankings(limit,context.weights,user_lat=context.lat,user_lon=context.lon)
