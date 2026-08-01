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
import csv
from pathlib import Path

CSV_FILE = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "data"
    / "cms"
    / "Hospital_General_Information.csv"
)

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

        with open(CSV_FILE , newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                hospital = Hospital(
                    cms_provider_id=row["Facility ID"],
                    name=row["Facility Name"],
                    hospital_type=row["Hospital Type"],
                    ownership_type=row["Hospital Ownership"],
                    emergency_services=row["Emergency Services"] == "Yes",
                )

                db.add(hospital)
                db.flush()

                db.add(
                    Location(
                        hospital_id=hospital.id,
                        address_line1=row["Address"],
                        city=row["City/Town"],
                        state=row["State"],
                        zip_code=row["ZIP Code"],
                    )
                )

                db.add(HospitalQuality(
                    hospital_id=hospital.id,

                    cms_overall_rating=int(row["Hospital overall rating"])
                    if row.get("Hospital overall rating","").isdigit()
                    else None,

                    mortality_group_measure_count=int(row["MORT Group Measure Count"])
                    if row.get("MORT Group Measure Count","").isdigit()
                    else None,

                    mortality_facility_measure_count=int(row["Count of Facility MORT Measures"])
                    if row["Count of Facility MORT Measures"].isdigit()
                    else None,

                    mortality_better=int(row["Count of MORT Measures Better"])
                    if row["Count of MORT Measures Better"].isdigit()
                    else None,

                    mortality_no_different=int(row["Count of MORT Measures No Different"])
                    if row["Count of MORT Measures No Different"].isdigit()
                    else None,

                    mortality_worse=int(row["Count of MORT Measures Worse"])
                    if row["Count of MORT Measures Worse"].isdigit()
                    else None,
                    )
                )
        db.commit()        
        print("Finished importing CMS hospitals.")
    finally:
        db.close()
        


if __name__ == "__main__":
    seed()

