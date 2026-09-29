"""GET /insurance — list of all insurance providers available for filtering."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository

router = APIRouter(tags=["insurance"])


@router.get("/insurance", response_model=list[str])
def list_insurance(db: Session = Depends(get_db)):
    return HospitalRepository(db).list_insurance()

@router.get('/insurance/categories')
def insurance_categories(db: Session = Depends(get_db)):
    from app.services.directory_taxonomy import insurance_carrier
    groups={}
    for name in HospitalRepository(db).list_insurance():
        groups.setdefault(insurance_carrier(name),[]).append(name)
    return [{'carrier':carrier,'plans':plans} for carrier,plans in sorted(groups.items())]
