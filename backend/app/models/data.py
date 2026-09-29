"""Provenance and refresh history; added without changing existing tables."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class HospitalMeasure(Base):
    __tablename__ = 'hospital_measures'
    __table_args__ = (UniqueConstraint('hospital_id', 'source_key', 'measure_id'),)
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(UUID(as_uuid=False), ForeignKey('hospitals.id'), index=True, nullable=False)
    source_key = Column(String, nullable=False)
    measure_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    comparison = Column(String)
    period_start = Column(String)
    period_end = Column(String)
    source_url = Column(String, nullable=False)

class DirectoryEntry(Base):
    __tablename__ = 'hospital_directory_entries'
    __table_args__ = (UniqueConstraint('hospital_id', 'kind', 'name'),)
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(UUID(as_uuid=False), ForeignKey('hospitals.id'), index=True, nullable=False)
    kind = Column(String, nullable=False)
    name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    source_label = Column(String, nullable=False)
    verified_on = Column(String, nullable=False)
    expires_on = Column(String)

class ImportRun(Base):
    __tablename__ = 'data_import_runs'
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_key = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default='running')
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime)
    row_count = Column(Integer, default=0)
    message = Column(String)
    checksum = Column(String)
    source_url = Column(String)

class HospitalPresence(Base):
    __tablename__ = 'hospital_cms_presence'
    hospital_id = Column(UUID(as_uuid=False), ForeignKey('hospitals.id'), primary_key=True)
    present = Column(Boolean, nullable=False)
    checked_on = Column(String, nullable=False)
    release_date = Column(String)
    checksum = Column(String, nullable=False)

class ReviewEvent(Base):
    """Append-only record of source checks and manual corrections."""
    __tablename__ = 'hospital_review_events'
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(UUID(as_uuid=False), ForeignKey('hospitals.id'), index=True, nullable=False)
    issue_type = Column(String, nullable=False)
    item_key = Column(String, nullable=False)
    action = Column(String, nullable=False)
    source_revision = Column(String)
    old_value = Column(String)
    new_value = Column(String)
    note = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
