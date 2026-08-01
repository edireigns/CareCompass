"""
Seeds Postgres with the mock hospital dataset (app/data/mock_hospitals.py)
so the API returns real rows out of the box. This stands in for the ETL
pipeline described in the spec until that's built.

Run with:
    python -m scripts.seed
(inside the backend container, or locally with DATABASE_URL pointed at
your Postgres instance)
"""
from app.db.session import Base, engine, SessionLocal
from app.models.hospital import (
    Hospital, Location, HospitalQuality, HospitalOutcomes,
    PatientExperience, WaitTimeEstimate, Specialty, Insurance,
)
from app.data.mock_hospitals import MOCK_HOSPITALS


def get_or_create(db, model, name):
    obj = db.query(model).filter(model.name == name).first()
    if obj:
        return obj
    obj = model(name=name)
    db.add(obj)
    db.flush()
    return obj


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Hospital).count() > 0:
            print("Hospitals already seeded, skipping.")
            return

        for record in MOCK_HOSPITALS:
            hospital = Hospital(
                name=record["name"],
                hospital_type=record["hospital_type"],
                ownership_type=record["ownership_type"],
                emergency_services=record["emergency_services"],
                trauma_level=record["trauma_level"],
                teaching_hospital=record["teaching_hospital"],
                pediatric_hospital=record["pediatric_hospital"],
            )
            db.add(hospital)
            db.flush()  # get hospital.id

            loc = record["location"]
            db.add(Location(hospital_id=hospital.id, **loc))

            db.add(HospitalQuality(hospital_id=hospital.id, **record["quality"]))
            db.add(HospitalOutcomes(hospital_id=hospital.id, **record["outcomes"]))
            db.add(PatientExperience(hospital_id=hospital.id, **record["experience"]))
            db.add(WaitTimeEstimate(hospital_id=hospital.id, **record["wait_time"]))

            for name in record["specialties"]:
                hospital.specialties.append(get_or_create(db, Specialty, name))
            for name in record["insurance_plans"]:
                hospital.insurance_plans.append(get_or_create(db, Insurance, name))

        db.commit()
        print(f"Seeded {len(MOCK_HOSPITALS)} hospitals.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
