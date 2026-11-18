---
name: inventory
description: Contributor mode for the Gaia data inventory. Use when the user types /inventory (alone, with a claim issue number, or with a description like "20 candidates in Africa"), says "inventory: start", names a dataset to check or add, or wants to take work from the queue.
---

# Inventory contributor mode

You help one person decide **how much work to take**, do it, and leave **one ledger file**. You never edit the inventory itself: CI rebuilds it from the ledger after merge. Work from the repo root.

## 1. Start: show the queue, let the user carve

1. If you don't know the user's GitHub handle, ask (it goes in `by` and the file name). Make sure they're on a branch, not `main`, after `git pull --rebase origin main`.
2. **`/inventory <issue number>`**: the user already has a claim. `python scripts/queue.py --issue <n>` lists its items; go to section 3.
3. **Otherwise** run `python scripts/queue.py` and show its overview as a short table: each kind of work, how many items are free, and the per-item estimate (minutes and tokens, with what the estimate is based on; say plainly when tokens were never measured). Then ask two things: **which kind**, and **how much they want to spend** (a number of items, or a time or token budget, which you turn into a number of items with the estimate).
4. Offer slices if they want to narrow it: `python scripts/queue.py --by region --kind candidate` (also `category`, `host`, `publisher`, `tier`). Filters: `--region`, `--category`, `--host`, `--publisher`, `--tier`, `--match <title text>`, `--wg` (working-group requests), `--fresh` (never touched). Same-host items are cheaper together (one site, one licence page), so a `--host` slice is a good default suggestion for `read` and `settle`.
5. Show what they'd get: `python scripts/queue.py --kind <k> [filters] --n <N>`. When they agree, claim it by adding `--claim`: this opens an issue assigned to them, and takes those items out of everyone else's view. Note the issue number.
6. **"A dataset I know"** needs no claim: go straight to packet a.
7. Note the start time. Don't read the big CSVs; use `queue.py` and `lookup.py`.

Kinds and packets: `read`, `settle`, `successor` = packet b; `schema` = c; `person-read` = d; `candidate` = e; a dataset the user names = a.

## 2. Finding things

- `python scripts/lookup.py "<name, DOI, URL or id>"`: best matches in the inventory and the candidate families. **Before proposing any new row**, check here: a score of 0.75 or more with the same publisher, or the same DOI root, means it's already in. Update that row instead.
- `python scripts/lookup.py --id <id>`: every non-empty field of one row (read its notes before re-checking it).

## 3. Limits per item (the user chose how many items; these bound each one)

| Packet | Fetches per item | Stop the item when |
|---|---|---|
| a | 4 | drafted, or blocked |
| b | 3 | checks settled, or blocked |
| c | 6 (metadata records first, then one documentation page) | packet filled, or a data file would be needed |
| d | 0 | the user has reported the page |
| e | 4 per family | a row or a verdict |

Stop the session at the user's budget (items, time or tokens), whichever comes first; write up what's done. Unfinished items go back to the queue when the claim closes. Per item: the landing page or repository record first, then at most two linked pages. Web search only to find a moved page's successor (`successor` items), and say so in the note.

**Records before pages.** These answer in one call and count as a read: Zenodo `/api/records/<id>` (check `access_right`: closed or restricted is `restricted`), figshare `/v2/articles/<id>`, Dataverse `/api/datasets/:persistentId/?persistentId=doi:<DOI as published>`, CKAN `/api/3/action/package_show?id=…` (and `datastore_search?resource_id=…&limit=0` for fields), Socrata `/api/views/<id>.json`, ArcGIS layer `?f=json`, Census `variables.json`, STAC collection JSON, FGDC or ISO XML metadata. A DataCite record alone does not settle a licence and gives publication years, not coverage.

**Blocked** (challenge page, 401/403/429, "enable JavaScript", empty shell; ICPSR, openICPSR and NaNDA always are): set no checks, note `blocked`, and tell the user it is `person-read` material. Never work around it.

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

One file per session: `ledger/<YYYY-MM-DD>-<handle>-<slug>.jsonl` (lowercase slug, e.g. `candidate-africa`), one JSON object per line.

**First line: what the session took** (this is how the estimates improve):
```json
{"meta": {"by": "handle", "kind": "candidate", "items": 15, "minutes": 34, "fetches": 52, "tokens": null, "claim": 23}}
```
`items` = items you finished; `minutes` from your start time; `fetches` = pages and records you fetched; `tokens` = ask the user to run `/cost` and give you the total, or leave null.

Every other record has `by`, `packet`, `ev` (the main URL you read) and `note` (what you read; anything odd).

**Update a row** (packets b, c, d):
```json
{"id": "us_cdc_places", "by": "handle", "packet": "b", "ev": "https://www.cdc.gov/places/...", "note": "licence and years from the methodology page",
 "set": {"chk_license": "pass", "chk_license_detail": "US federal (CDC), no other terms", "chk_license_evidence": "https://...",
         "license_confirmed": "public domain (US Government work)", "license_class": "public_domain_us_federal"}}
```

**New row** (packets a and e): add `"new": true`; `id` = `<country>_<publisher>_<product>` (lowercase, underscores; `global_…`, `eu_…` for multinational); set at least `dataset_name`, `organization`, `site_url`, `category` (use the category of a similar row: `lookup.py --id`), `region`, `"round": "contrib"`, `persistent_id` (the DOI, if any), and every check you read. One row per **product family**: list sibling DOIs or versions in `notes`.

**Rule out a candidate** (packet e only), instead of a row:
```json
{"candidate": "10.5281/zenodo.123", "verdict": "not_place_data", "reason": "a paper's figures, no place-keyed data", "by": "handle", "packet": "e", "ev": "https://zenodo.org/api/records/123", "note": "..."}
```
Verdicts: `not_place_data`, `not_a_dataset` (paper, code, slides), `out_of_scope` (not health-relevant, or microdata of individuals), `restricted`, `blocked`, `duplicate_of:<inventory id>`. Every family you finish ends as a row (new, or an update to an existing one with the family's DOI in `notes`) or a verdict.

**Schema records** (packet c): set `schema_source` (the record URL), `schema_checked_on` (today), `place_key_system`, `place_key_vintage`, and where empty `columns_found` (semicolon list, first 40), `place_key_found`, `geometry_found`, `crs`, `years_found`. Also write `ledger/packets/<id>.json`:
`{"id", "schema_source", "route", "columns": [{"name", "type", "meaning"}], "place_key": {"column", "system", "level", "vintage", "basis"}, "geometry": {"kind": "embedded|reference|none", "type", "crs", "reference"}, "years_found", "not_read": ["sample_rows", "value_coding", "missing_coding"], "evidence": [urls], "notes"}`. A schema read is not a page verification: don't set `verification_level` or `file_verified`.

**Person-read** (packet d): the user tells you what the page says; you write the record with the user's URL as evidence and `"note": "person-read by <handle>"`. If the page opens for a person and that was the only blocker, set `url_health` to `ok-browser`.

**Never set:** `verify_tier`, `tier`, `health_score`, `checks_*`, `all_passing`, `verify_blockers`, `verified_on`, `partB_*`, `tier_cap`, or `round` on an existing row.

## 6. Finish

1. `python scripts/validate.py --changed --against origin/main`. Fix every error. If it says a row was changed on main since you branched, run `lookup.py --id` for that row, reconsider your record, then `git rebase origin/main`.
2. Tell the user in 3-5 lines: items done against items claimed, checks settled, rows added, candidates ruled out, what was blocked, anything that looked wrong in an existing row, and what the session took against the estimate.
3. Suggest: `git add ledger/ && git commit -m "Inventory: <kind> (<n> items)"`, push, and `gh pr create --title "Inventory: <kind>, <n> items" --body "Closes #<claim issue>. <your summary>"`. Do it only if the user asks. No AI attribution lines.
