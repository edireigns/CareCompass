# CareCompass

CareCompass is a local hospital search and comparison app built with React, FastAPI, and PostgreSQL. It combines imported CMS hospital data with source-reviewed location, insurance-plan, and specialty records. Rankings are preference aids based on available historical measures; they are not clinical recommendations.

## Start the local app

Double-click `CareCompass.cmd` and choose **Start both servers**. The launcher checks the database and dependencies, starts the backend and frontend, and opens `http://127.0.0.1:5174`. See [RECOVERY.md](RECOVERY.md) for setup, backup verification, and restore instructions. Keep `backend/.env` private and do not commit it.

The Git repository contains source code and selected small provenance files. It does **not** contain your live PostgreSQL database or the large downloaded CMS measure extracts. On a new computer, restore a verified database archive separately. Data Refresh can download current CMS releases when internet access is available.

## What works

- Search by city, ZIP, specialty category, exact verified plan, or nearby location.
- Adjust ranking weights; view score contributions, data completeness, and reporting periods.
- Open hospital profiles and compare hospitals while preserving search and ranking preferences.
- Review source-linked insurance plans and clinical specialties; unknown coverage remains unknown.
- Refresh CMS data, review unmatched addresses and stale records, and keep correction history.
- Create database backups, optionally copy them to another drive, and verify an archive by restoring it into a disposable schema.

[DATA_GUIDE.md](DATA_GUIDE.md) explains sources and coverage. The verified Chicago records in `backend/app/data/verified` are partial and should not be treated as an exhaustive provider directory. Confirm an exact plan and provider with the insurer before care.

## Run checks

From `backend`, run `.\.venv\Scripts\python.exe -m pytest tests -q`. The browser journey test also requires Playwright (`.\.venv\Scripts\python.exe -m pip install -r requirements-e2e.txt`) and Chrome or Edge. From `frontend`, run `npm.cmd install` and `npm.cmd run build`.

## Hosting status

The local Docker Compose and Dockerfiles are development scaffolding: they use mock seeding or reload mode and should not be used unchanged for a public deployment. The admin endpoints are intentionally restricted to the local computer. A public deployment needs a managed PostgreSQL database, a data migration, durable storage for any files written at runtime, and authenticated administration or a read-only public mode.
