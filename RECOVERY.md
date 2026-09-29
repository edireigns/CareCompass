# Start, back up, and recover CareCompass

Double-click **CareCompass.cmd** in this folder and choose **1**. The launcher checks Python packages, the database, Node.js, frontend files and ports before opening http://127.0.0.1:5174. If both CareCompass servers are already healthy, it opens the existing app. Otherwise keep its window open. Press Ctrl+C to stop both servers it started, then choose 6 to exit.

The launcher serves the tested frontend build. After editing frontend source, run `npm.cmd run build` in `frontend` before launching. Backend code changes take effect when you restart. It never kills an unrelated process or automatically recreates the database.

## If startup fails

- **Missing packages:** in `backend`, run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **Missing Python environment:** in `backend`, run `py -3 -m venv .venv`, then the package command above.
- **Database unavailable:** start the PostgreSQL Windows service and check `backend/.env`. Keep that file private. The launcher does not print its connection string.
- **Port 8000 or 5174 occupied:** stop the old CareCompass terminal with Ctrl+C. If another application owns that port, close or reconfigure it yourself.
- **Frontend missing:** run `npm.cmd install` and `npm.cmd run build` in `frontend`.
- **Server exits:** read `logs/backend.log` or `logs/frontend.log`. These files are replaced on each launcher start.

## Backups

Choose **2** in the launcher, or **Back up now** on Data Refresh. Each backup is a PostgreSQL custom archive in `backups/`, with a JSON file containing its timestamp, purpose and SHA-256 checksum. Archive readability is checked before reporting success. PostgreSQL command-line tools (`pg_dump`, `pg_restore`) must be installed; the app also searches the standard Windows PostgreSQL installation folder.

A backup is mandatory before a refresh, verified-directory upload, correction or restore. If backup fails, that operation stops. Existing archives are never automatically deleted. Use launcher option **5** or the Data Refresh page to select an existing folder on another drive or network share. Leave it unset until that drive is ready. Once enabled, every new backup is copied there and checksum-checked; an unavailable destination stops data changes. The setting is stored in `backup-settings.json`. Database archives contain the database, not application code, downloaded CSV files, or `.env`; preserve those separately.

Choose launcher option **4** or **Verify restore** beside an archive on Data Refresh to test a backup. This checks the checksum, restores into a temporary schema in the configured PostgreSQL database, compares table counts, checks that the live hospital count has not changed, and writes a `.verification.json` report beside the archive. It requires PostgreSQL `pg_restore` and `psql`. A passing restore verification does not replace the live database.

## Restore

Stop both servers. Double-click **CareCompass.cmd**, choose **3**, and select an archive. Review its name and date; type **RESTORE** only if you intend to replace the configured database. The tool checks the archive checksum, saves a fresh safety backup, and rebuilds the app's public schema in one transaction. This also removes tables introduced after an older backup was created. A PostgreSQL restore error rolls back that transaction. Keep the `.dump` and matching `.json` together. Use a dedicated CareCompass database; do not share its public schema with unrelated applications. Restore also requires the PostgreSQL `psql` tool and database-owner access.

Restart using option 1. Refresh the browser after restoring. Do not run other database imports while restoring.

## Review queue and automated checks

Data Refresh contains a review queue for unmatched hospital addresses, directory records needing rechecking, and hospitals missing from the latest complete CMS release. Use a source URL and note for each review. Address corrections require verified coordinates; insurance and specialty corrections keep exact source names. Every action is recorded in correction history. Reviews of CMS absence do not change a hospital's operating status. Manual coordinate corrections are also saved to `backend/app/data/cms/Hospital_Coordinates.csv` for later refreshes.

Run backend checks from `backend` with `.\.venv\Scripts\python.exe -m pytest tests -q`. The browser journey additionally needs Playwright (`.\.venv\Scripts\python.exe -m pip install -r requirements-e2e.txt`), frontend npm packages, and Chrome or Edge. It creates a temporary SQLite database and separate local servers; it never refreshes the live CareCompass database.

## Coverage and freshness policies

The first verified local directory file is `backend/app/data/verified/chicago-2026-09-28.csv`: 19 plan records for Northwestern Memorial and UChicago Medicine, and 21 clinical specialty records for Northwestern Memorial and Rush. Each row links to a hospital-published source checked September 28, 2026. This is partial coverage. Hospital plan participation does not establish physician participation or coverage for every service. Year-specific 2026 plans expire in the app on December 31, 2026; undated records do not get an invented expiry.

Measure reporting periods ending more than 730 days ago are labelled older. Directory records checked more than 180 days ago are labelled for rechecking. Expired entries stay visible as evidence and are excluded from current insurance/specialty filters. Source imports older than 180 days prompt a refresh. These are CareCompass display policies, not official CMS quality thresholds.

CMS directory membership is compared only against a hash-verified, complete official download. Missing hospitals are retained and marked “not listed”; this does not establish closure. A local file without download provenance does not update membership flags.

Coordinates remain address estimates from the Census geocoder. Mailbox and suite suffixes may be removed from the query; original CMS addresses and queried addresses remain in the cache. Unmatched addresses remain unknown and are excluded from nearby search. `backend/app/data/cms/Unmatched_Address_Review.csv` lists the remaining records needing address research.

The September 28 update obtained 27 new or corrected address matches, including hospital-published address corrections for Rush and La Rabida. There are 4,654 coordinate records across 5,445 retained hospitals. The July 22 CMS directory contains 5,419 hospitals; 26 older records are retained but marked absent. Of the hospitals in that latest directory, 786 still need coordinate verification. Their locations were not guessed.
