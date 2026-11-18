---
name: inventory
description: Contributor mode for the Gaia data inventory. Use when the user types /inventory (with or without a batch id like BR-03 or CA-02), says "inventory: start", names a dataset to check or add, or wants to work a batch.
---

# Inventory contributor mode

You help one person finish **one packet** and leave **one ledger file**. You never edit the inventory itself: CI rebuilds it from the ledger after merge. Work from the repo root.

## 1. Start (short)

1. If you don't know the user's GitHub handle, ask (it goes in `by` and in the file name).
2. **With a batch id** (`/inventory BR-03`): run `python scripts/lookup.py --batch BR-03`. The prefix sets the packet: BR, SO, FS = b; RR = c; BN = d; CA = e. Check the batch issue is assigned to the user (`gh issue list --label batch --search "BR-03"`); if it's assigned to someone else, stop and say so.
3. **Without one**: show the menu, one line each: (a) a dataset I know, (b) settle a batch of rows, (c) recipe-ready schemas, (d) person-read of blocked pages, (e) check candidate families. For b-e, run `python scripts/lookup.py --batches` and suggest the lowest-numbered unassigned batch.
4. Make sure the user is on a branch, not `main` (`git switch -c batch/<id>-<handle>` if needed), and `git pull --rebase origin main` first.
5. Say the caps for the packet (section 3), then start. Don't read the big CSVs; use `lookup.py`.

## 2. Finding things

- `python scripts/lookup.py "<name, DOI, URL or id>"`: best matches in the inventory and the candidate families. **Before proposing any new row**, check here: a score of 0.75 or more with the same publisher, or the same DOI root, means it's already in. Update that row instead.
- `python scripts/lookup.py --id <id>`: every non-empty field of one row (read the row's notes before re-checking it).

## 3. Caps

| Packet | Items | Fetches | Stop when |
|---|---|---|---|
| a | 1 row | 4 | drafted, or blocked |
| b | the batch (10) | 3 per row, 30 total | batch done, or 45 min |
| c | the batch (5) | 6 per row (metadata records first, then one documentation page) | packets filled, or a data file would be needed |
| d | as many as the user reports | 0 | the user stops |
| e | the batch (10 families) | 4 per family, 40 total | batch done, or 45 min |

Per item: the landing page or repository record first, then **at most two** linked pages (metadata, data dictionary, licence, download page, API record). Web search only to find a moved page's successor (packet b, FS batches), and say so in the note.

**Records before pages.** These answer in one call and count as a read: Zenodo `/api/records/<id>` (check `access_right`: closed or restricted is `restricted`), figshare `/v2/articles/<id>`, Dataverse `/api/datasets/:persistentId/?persistentId=doi:<DOI as published>`, CKAN `/api/3/action/package_show?id=…` (and `datastore_search?resource_id=…&limit=0` for fields), Socrata `/api/views/<id>.json`, ArcGIS layer `?f=json`, Census `variables.json`, STAC collection JSON, FGDC or ISO XML metadata. A DataCite record alone does not settle a licence and gives publication years, not coverage.

**Blocked** (challenge page, 401/403/429, "enable JavaScript", empty shell; ICPSR, openICPSR and NaNDA always are): set no checks, note `blocked`, and tell the user it can be a packet d. Never work around it.

## 4. Judging the checks

Full definitions: `method/BRIEF-page-reads.md` ("The checks"). Values: `pass`, `warn`, `fail`, `n.a.`, `not_checked`. Every check you set gets `<check>_detail` (what you read, a few words) and `<check>_evidence` (the URL). Leave what you didn't read alone.

- **chk_license**: pass = open or attribution-only; warn = non-commercial, registration, a named licence whose text you didn't read, or site-wide terms only; fail = restricted or none stated. Set `license_confirmed` (exact) and `license_class` (`open`, `attribution`, `non-commercial`, `registration`, `restricted`, `unknown`, or `public_domain_us_federal` for a US federal publisher on a .gov page; labs, DAACs, Smithsonian and multi-provider portals need the page's own statement).
- **chk_temporal / chk_recency**: `temporal_confirmed`, `latest_year_confirmed`; recency pass = 2020 or later or ongoing, warn = 2000-2019, fail = before 2000 or discontinued.
- **chk_unit**: `finest_unit_confirmed` from `method/unit-vocabulary.csv` only (grids as `grid_<res>`, e.g. `grid_1km`).
- **chk_access**: pass = open download or keyless API; warn = registration or API key; fail = on request or restricted. `access_confirmed`.
- **chk_join_key**: a standard key (GEOID/FIPS, ZCTA, LSOA/MSOA, NUTS, admin or P-codes, lat/lon) or geometry, shown in the dictionary or record. `join_key_confirmed`.
- **chk_format_gaia**: a GDAL-loadable format (shp, gpkg, geojson, gdb, csv/xlsx with a key or coordinates, geoparquet, geotiff, netcdf). `formats_confirmed`.
- **chk_withdrawn**: pass only from evidence (a live record or page with no withdrawal notice).
- **chk_link_live**: pass if the page you read loaded.
- **Place key, when you see it:** `place_key_system` (e.g. `us_tract_geoid`, `zcta`, `lsoa`, `nuts`, `ocha_pcode`, `coordinates`, `embedded geometry`) and `place_key_vintage` only from evidence (a column like `GEOID20`, or text like "2020 census tracts"); never infer the vintage from the data year.

## 5. The ledger file

One file per session: `ledger/<YYYY-MM-DD>-<handle>-<batch or slug>.jsonl` (lowercase slug), one JSON object per line. Every record has `by`, `packet`, `batch` (if any), `ev` (the main URL you read) and `note` (what you read; anything odd).

**Update a row** (packets b, c, d):
```json
{"id": "us_cdc_places", "by": "handle", "packet": "b", "batch": "SO-04", "ev": "https://www.cdc.gov/places/...", "note": "licence and years from the methodology page",
 "set": {"chk_license": "pass", "chk_license_detail": "US federal (CDC), no other terms", "chk_license_evidence": "https://...",
         "license_confirmed": "public domain (US Government work)", "license_class": "public_domain_us_federal"}}
```

**New row** (packets a and e): add `"new": true`; `id` = `<country>_<publisher>_<product>` (lowercase, underscores; `global_…`, `eu_…` for multinational); set at least `dataset_name`, `organization`, `site_url`, `category` (from the 14 categories in use: run `python scripts/lookup.py --id <a similar row>` to see one), `region`, `"round": "contrib"`, `persistent_id` (the DOI, if any), and every check you read. One row per **product family**: list sibling DOIs or versions in `notes`.

**Rule out a candidate** (packet e only), instead of a row:
```json
{"candidate": "10.5281/zenodo.123", "verdict": "not_place_data", "reason": "a paper's figures, no place-keyed data", "by": "handle", "packet": "e", "batch": "CA-02", "ev": "https://zenodo.org/api/records/123", "note": "..."}
```
Verdicts: `not_place_data`, `not_a_dataset` (paper, code, slides), `out_of_scope` (not health-relevant, or microdata of individuals), `restricted`, `blocked`, `duplicate_of:<inventory id>`. Every family in the batch ends as either a row (new, or an update to an existing one with the family's DOI in `notes`) or a verdict.

**Schema records** (packet c): set `schema_source` (the record URL), `schema_checked_on` (today), `place_key_system`, `place_key_vintage`, and where empty `columns_found` (semicolon list, first 40), `place_key_found`, `geometry_found`, `crs`, `years_found`. Also write `ledger/packets/<id>.json`:
`{"id", "schema_source", "route", "columns": [{"name", "type", "meaning"}], "place_key": {"column", "system", "level", "vintage", "basis"}, "geometry": {"kind": "embedded|reference|none", "type", "crs", "reference"}, "years_found", "not_read": ["sample_rows", "value_coding", "missing_coding"], "evidence": [urls], "notes"}`. A schema read is not a page verification: don't set `verification_level` or `file_verified`.

**Person-read** (packet d): the user tells you what the page says; you write the record with the user's URL as evidence and `"note": "person-read by <handle>"`. If the page now opens and was the only blocker, set `url_health` to `ok-browser`.

**Never set:** `verify_tier`, `tier`, `health_score`, `checks_*`, `all_passing`, `verify_blockers`, `verified_on`, `partB_*`, `tier_cap`, or `round` on an existing row.

## 6. Finish

1. `python scripts/validate.py --changed --against origin/main`. Fix every error. If it says a row was changed on main since you branched, run `lookup.py --id` for that row, reconsider your record, then `git rebase origin/main`.
2. Tell the user in 3-5 lines: items done, checks settled, rows added, candidates ruled out, what was blocked (packet d material), anything that looked wrong in an existing row.
3. Suggest: `git add ledger/ && git commit -m "Inventory: <batch> (<n> rows)"`, push, and `gh pr create --title "Inventory: <batch>" --body "Closes #<issue>. <your 3-line summary>"`. Do it only if the user asks. No AI attribution lines.
