# CareCompass data management

Open **Data Refresh** (`http://localhost:5174/admin`) while the backend and frontend are running locally.

## Loaded data

- CMS hospital directory and star ratings.
- HCAHPS patient experience: top-box satisfaction, recommendation, nurse/doctor communication, and cleanliness percentages.
- CMS mortality, hip/knee replacement complications, patient-safety measures, infection ratios, readmissions, and historical ED visit durations. Each detailed measure shows its unit, reporting period, and source.
- U.S. Census address-matched coordinates for nearby search. Unmatched hospitals remain searchable by city or ZIP, but do not appear in nearby results. Distance is straight-line distance, not travel time.
- Psychiatry, pediatrics, and long-term hospital care from explicit CMS facility types. These are facility classifications, not a complete clinical specialty directory.

The initial import contains 5,432 hospitals, 4,640 coordinate matches, 111,324 numeric detailed measures and patient-experience data for 3,956 hospitals. CMS suppresses or does not report some measures; these stay unknown. Infection SIR values are observed/expected ratios, not percentages. ED duration is a historical median, not current waiting time.

## Refreshing

**Refresh now** imports saved CSVs in `backend/app/data/cms`. Select **Download the latest CMS releases** to download official releases first, or **Retry unmatched hospital addresses** to contact the Census geocoder. Keep the backend running until completion. Downloads and geocoding require internet access and can take several minutes.

Refresh preserves hospital IDs and commits each source separately. A failed source retains its prior database records and shows an error. Hospitals absent from a later directory release are retained to preserve existing references; they are not automatically deleted. After an interrupted server restart, retry a stopped refresh. The source table records completed imports and their dates; measure reporting periods may be older than those dates.

Data-changing endpoints require localhost access and the `X-CareCompass-Admin: 1` header, which the local frontend supplies. This is local administration, not a multi-user authentication system.

## Verified insurance and specialty CSV

Download the blank template on Data Refresh. Required columns:

```csv
facility_id,kind,name,source_url,source_label,verified_on,expires_on
```

- `facility_id`: the hospital's CMS Facility ID, shown on its profile. Preserve leading zeros.
- `kind`: `insurance` or `specialty`.
- `name`: exact insurance plan/network or specialty name.
- `source_url`: an HTTP(S) provider-directory or hospital source you personally checked.
- `source_label`: readable name of that source.
- `verified_on`: date checked, `YYYY-MM-DD`; cannot be in the future.
- `expires_on`: optional date in the same format, on or after verification.

Select the file, inspect the preview, then choose **Import verified records**. Files may contain 1–5,000 records and be at most 3 MB. Every facility ID and record is validated before importing. Reimporting the same facility, kind and name updates its evidence without creating duplicate memberships. To withdraw a record, import it with an expired date and a verification date no later than that expiry. Expired evidence remains visible for context and is excluded from active filters and accepted-plan lists.

No insurance memberships are invented or inferred from CMS measures. An empty insurance list means **unknown**, not rejected. The importer requires source evidence but does not independently certify its truth; the person importing it must verify the source and exact plan. Confirm coverage with the insurer before choosing care.

## Rankings

Moving a priority slider recalculates the top ten across the full directory. Set a location to enable distance. Missing measurements are excluded and available weights are normalized to 100%. With no usable selected measures, a hospital has no score. Weighted coverage is the available share of your selected priorities. Score-sorted lists place hospitals with at least 50% coverage before those below 50%, then sort by score within each group. Nearby lists remain ordered by distance.

Expand **Score explained** on a result or profile to see raw values, missing measures, chosen weights, applied weights, formulas and contributions. Coverage measures completeness, not clinical quality. Scores are a prototype preference aid, not a validated clinical recommendation: quality uses stars/5, ED duration is capped at 600 minutes, distance at 50 miles, readmissions at 25%, and satisfaction uses its reported percentage.

Location, city/ZIP and directory filters, radius, priorities and comparison selections are retained in this tab's session storage across navigation and reloads. They are not saved to a user account. **Reset all preferences** clears them together; **Clear location** removes the location and disables its weight. Use **Add to comparison** on results or profiles to select up to five hospitals. Search, rankings, nearby results, profiles and comparisons use the same saved ranking preferences and show scores to one decimal place. Browser session restoration may restore tab session storage; use Reset all preferences whenever you want to clear it explicitly.

## Checks

From `backend`, run `.\.venv\Scripts\python.exe -m pytest tests -q`. The data-feature regression tests use an isolated SQLite database, not your project database. From `frontend`, run `npm.cmd run build` for TypeScript and production build checks.


## Chicago coverage and score dates (September 29, 2026)

The Chicago coverage panel appears on Data Refresh and Chicago search. Its denominator is hospitals whose CMS directory location is Chicago, IL and whose presence is confirmed in the latest imported release. It is not the Chicago metropolitan area. Counts indicate at least one sourced record, never an exhaustive insurance or specialty directory. CMS facility classifications are excluded from clinical coverage counts. Source checks include explicit retrieval failures and outdated sources; they do not certify full coverage.

Additional curated evidence is in `backend/app/data/verified/chicago-expanded-2026-09-29.csv`. Hospital-by-hospital source notes are in `chicago-review.json`. Source labels retain original clinical or plan wording; a carrier heading is prepended when needed to preserve the source's hierarchy. Undated plan pages are labeled as such. No carrier-only acceptance is expanded to all its products. Weiss, Thorek Andersonville and La Rabida insurance gaps remain explicit because their linked lists have obsolete products or an old revision date.

Specialty categories are broad search aids. Exact clinical labels, pediatric scope and referral notes remain in source evidence. Insurance carrier grouping is navigation only: exact plan strings, tiers and years remain separate filters. No plan equivalence is inferred.

Score reporting dates attach only to available, positively weighted components. ED duration, satisfaction and readmission dates require an unambiguous match to the measure used by the summary. Unmatched or ambiguous dates stay unknown. The CMS directory release date is not represented as an overall-rating clinical period. The two-year age flag describes reporting-period end dates, not the time the data was downloaded. Distance is calculated rather than a clinical measure. These labels do not change scores or weights.

Swedish Hospital's map point comes from its official location page's JSON-LD for the public entrance at 5140 N. California Avenue, connected to the CMS main-building address at 5145. Provenance is retained in `swedish-entrance-coordinate.json` and the coordinate cache. This is an approximate campus location, not navigation to an emergency entrance.
