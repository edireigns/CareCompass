"""
CareCompass API entrypoint.

Wires together config, CORS, and all route modules. Run locally with:
    uvicorn app.main:app --reload
or via `docker compose up` from the project root.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import (
    search, nearby, hospital, compare, recommend, specialties, insurance, rankings,ai,data,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("carecompass")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Aggregates public healthcare datasets into personalized hospital recommendations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(nearby.router, prefix=settings.api_v1_prefix)
app.include_router(hospital.router, prefix=settings.api_v1_prefix)
app.include_router(compare.router, prefix=settings.api_v1_prefix)
app.include_router(recommend.router, prefix=settings.api_v1_prefix)
app.include_router(specialties.router, prefix=settings.api_v1_prefix)
app.include_router(insurance.router, prefix=settings.api_v1_prefix)
app.include_router(rankings.router, prefix=settings.api_v1_prefix)
app.include_router(ai.router, prefix=settings.api_v1_prefix)
app.include_router(data.router, prefix=settings.api_v1_prefix)

@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.on_event("startup")
def on_startup():
    # Add provenance tables without replacing the recovered hospital database.
    from app.db.session import Base, engine
    from app.models.data import HospitalMeasure, DirectoryEntry, ImportRun, HospitalPresence, ReviewEvent
    Base.metadata.create_all(bind=engine, tables=[HospitalMeasure.__table__, DirectoryEntry.__table__, ImportRun.__table__, HospitalPresence.__table__, ReviewEvent.__table__])
    logger.info("%s starting in %s mode", settings.app_name, settings.app_env)
