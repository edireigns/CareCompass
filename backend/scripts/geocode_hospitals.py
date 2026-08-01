"""
Adds latitude and longitude to hospital locations using the
U.S. Census batch geocoding service.

Run inside Docker with:
    python -m scripts.geocode_hospitals
"""

import csv
import io
import time

import httpx

from app.db.session import SessionLocal
from app.models.hospital import Hospital, Location


CENSUS_BATCH_URL = (
    "https://geocoding.geo.census.gov/"
    "geocoder/locations/addressbatch"
)

BATCH_SIZE = 500
MAX_RETRIES = 3


def create_batch_file(locations: list[Location]) -> str:
    """
    Creates the temporary CSV required by the Census geocoder.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    for location in locations:
        writer.writerow(
            [
                str(location.id),
                location.address_line1 or "",
                location.city or "",
                location.state or "",
                location.zip_code or "",
            ]
        )

    return output.getvalue()


def parse_coordinates(value: str) -> tuple[float, float] | None:
    """
    Census returns coordinates as:
        longitude,latitude
    """

    if not value or "," not in value:
        return None

    try:
        longitude_text, latitude_text = value.split(",", maxsplit=1)

        latitude = float(latitude_text.strip())
        longitude = float(longitude_text.strip())

        return latitude, longitude

    except ValueError:
        return None


def send_batch(
    client: httpx.Client,
    locations: list[Location],
) -> str:
    """
    Sends one batch to the Census geocoder.

    Retries the request if the server times out.
    """

    batch_csv = create_batch_file(locations)

    files = {
        "addressFile": (
            "hospital_addresses.csv",
            batch_csv,
            "text/csv",
        )
    }

    data = {
        "benchmark": "Public_AR_Current",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.post(
                CENSUS_BATCH_URL,
                files=files,
                data=data,
            )

            response.raise_for_status()
            return response.text

        except httpx.TimeoutException:
            print(
                f"Request timed out. "
                f"Retry {attempt} of {MAX_RETRIES}."
            )

            if attempt == MAX_RETRIES:
                raise

            time.sleep(5)

    raise RuntimeError("The Census geocoder request failed.")


def save_batch_results(
    response_text: str,
    locations: list[Location],
) -> tuple[int, int]:
    """
    Reads one Census response and updates the matching Location objects.
    """

    locations_by_id = {
        str(location.id): location
        for location in locations
    }

    reader = csv.reader(io.StringIO(response_text))

    matched = 0
    unmatched = 0

    for row in reader:
        if len(row) < 6:
            unmatched += 1
            continue

        location_id = row[0].strip()
        match_status = row[2].strip()
        coordinates_text = row[5].strip()

        location = locations_by_id.get(location_id)

        if location is None:
            unmatched += 1
            continue

        if match_status.lower() != "match":
            unmatched += 1
            continue

        coordinates = parse_coordinates(coordinates_text)

        if coordinates is None:
            unmatched += 1
            continue

        latitude, longitude = coordinates

        location.latitude = latitude
        location.longitude = longitude

        matched += 1

    return matched, unmatched


def geocode_hospitals() -> None:
    db = SessionLocal()

    total_matched = 0
    total_unmatched = 0

    try:
        locations = (
            db.query(Location)
            .join(Hospital)
            .filter(
                Location.latitude.is_(None),
                Location.longitude.is_(None),
                Location.address_line1.is_not(None),
            )
            .order_by(Location.id)
            .all()
        )

        if not locations:
            print("No hospital locations need geocoding.")
            return

        total_locations = len(locations)
        total_batches = (
            total_locations + BATCH_SIZE - 1
        ) // BATCH_SIZE

        print(
            f"Found {total_locations} hospital addresses."
        )

        timeout = httpx.Timeout(
            connect=30.0,
            read=300.0,
            write=60.0,
            pool=30.0,
        )

        with httpx.Client(timeout=timeout) as client:
            for batch_number, start in enumerate(
                range(0, total_locations, BATCH_SIZE),
                start=1,
            ):
                batch = locations[
                    start : start + BATCH_SIZE
                ]

                print(
                    f"Processing batch "
                    f"{batch_number}/{total_batches} "
                    f"({len(batch)} addresses)..."
                )

                try:
                    response_text = send_batch(
                        client,
                        batch,
                    )

                    matched, unmatched = save_batch_results(
                        response_text,
                        batch,
                    )

                    total_matched += matched
                    total_unmatched += unmatched

                    db.commit()

                    print(
                        f"Batch finished: "
                        f"{matched} matched, "
                        f"{unmatched} unmatched."
                    )

                except Exception as error:
                    db.rollback()

                    print(
                        f"Batch {batch_number} failed: "
                        f"{error}"
                    )

                time.sleep(1)

        print("")
        print("Geocoding finished.")
        print(
            f"Coordinates saved: {total_matched}"
        )
        print(
            f"Addresses not matched: {total_unmatched}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    geocode_hospitals()