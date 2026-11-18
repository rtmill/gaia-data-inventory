# PROMPT 7: schema and place-key pass over the recipe-ready queue (TODO 2.16, first rung; feeds 3.11)

Claude Code prompt. Run from `D:\workspace\gaia` in a fresh session, on Sonnet (`/model sonnet`). Unattended. **Time box: about 2 hours in total, with a cap for each phase.** Run the phases in order, one at a time. **No sub-agents.** Run this job alone: only one job writes inventory masters at a time.

> **This assumes:** (1) a machine-readable metadata record (ArcGIS, Socrata, CKAN, repository API, Census `variables.json`, OGC capabilities) states a dataset's columns and place key faithfully enough to start a recipe; (2) the recipe-ready queue (licence, access, join key and format all `pass`, no file opened) is the right first set; (3) this pass reads metadata only: no sample rows, no value coding, no downloads (Robert, 2026-11-18).

## Context

- **Master:** the newest `docs/discovery/inventory-combined-*.csv` by date suffix (at writing, `inventory-combined-2026-11-03-p6e.csv`, 805 rows). Ignore `round = 2-pilot`.
- **Targets:** `publish/OHDSI-GIS/exploration/place-data-inventory/queues/recipe-ready.csv` (85 rows: Gold 38, Silver 47; WG-request rows first, then Gold, then id). If the master is newer than the queue, regenerate it first: `python docs/discovery/onramp/method/scripts/make_queues.py <master> <tmpdir>`.
- **Question:** for each target, what are the columns, which column is the place key, which **system, level and vintage** is that key (e.g. `us_tract_geoid`, tract, 2020), what geometry ships with it (type, CRS) or what it must join to, and what years the data covers, all from metadata alone? Second question: **is metadata enough**, or do recipes need a file read (the next rung)?
- **Why now:** Robert and Jared agreed (2026-11-17) to stabilise the recipe format first; gaiaCatalog #44 is the draft recipe profile v0.1. Only 15 rows have ever had a file opened, and only 4% of Gold/Silver rows state a key vintage (#23). This pass gives #44 real inputs and fills TODO 3.11's `place_key_system` / `place_key_vintage`.
- Read first: `run-p6-placekey/report.md` and `run-p6-placekey/k0.py` (key classification logic; reuse it), `fileverify/fileverify-report-2026-10-29.md` (what metadata vs files showed last time), `unit-vocabulary.csv`, the "Rules" section of `PROMPT-4-publisher-fanout.md`, and `publish/catalog-drafts-2026-11-03/README.md` (what a draft recipe needs).

| Phase | Target | Cap | Time |
|---|---|---|---|
| S0 | Classify each target's metadata endpoint (script); test one per kind | | 15 min |
| S1 | Harvest metadata records (script) | 85 rows, 6 requests per row, 400 in all | 40 min |
| S2 | Parse schema, key, geometry, years (script plus hand check) | | 20 min |
| S3 | Agent reads where scripts found no schema | 20 rows, 3 pages per row | 25 min |
| S4 | Merge, numbers check, report, docs (always runs) | | 20 min |

## Rules (every phase)

Same as PROMPT-4 "Rules", with the run folder `docs/discovery/run-p7-schema/`. In short:
- Writes only to the run folder until S4.
- Evidence URL for every value (the metadata record's URL, not the landing page, when the value came from the record).
- No downloads of data files, no sign-ins, no API keys, no registrations, no bot-check workarounds. A record that needs a key or login is `gated`, not worked around.
- 1 request per second per host; the inventory user-agent string; 20 s timeout, 1 retry.
- Checkpoint every 10 rows in `checkpoint.jsonl`. If a cap or usage limit stops a phase, don't retry: go to S4.
- Don't change `tier_of()`, the federal licence rule, or any `chk_*` value. **This pass changes no tiers.** Where metadata contradicts a page-verified value (key, unit, years, format), write it to `contradictions.csv` for Robert; don't fix it.

## S0: classify endpoints (script)

For each target, from `access_url`, `site_url`, `file_url`, `formats_confirmed`, `persistent_id` and `notes`, pick the metadata route, in this order of preference:

| Kind | Record to fetch |
|---|---|
| ArcGIS item / feature or map service | `<service>/<layer>?f=json` (fields, geometryType, spatialReference, extent); item `?f=json` for dates |
| Socrata | `/api/views/<id>.json` (columns with names, types, descriptions) |
| CKAN | `/api/3/action/package_show?id=…`; datastore `datastore_search?resource_id=…&limit=0` gives fields without rows |
| Zenodo / figshare / Dataverse | `/api/records/<id>`; `/v2/articles/<id>`; Dataverse dataset JSON plus `/api/access/datafile/<id>/metadata/ddi` for variables (metadata only) |
| US Census API | `https://api.census.gov/data/<year>/<dataset>/variables.json` and `geography.json` (metadata; test whether they need a key) |
| OGC WFS / WMS / WCS | `GetCapabilities`; WFS `DescribeFeatureType` |
| STAC | collection JSON (`summaries`, `extent`, asset `type`) |
| Data dictionary page or PDF | S3 (agent read) |
| None | `no_metadata` (S3 candidate) |

Write `s0-routes.csv` (id, kind, record_url, basis). Test one record per kind once and write `endpoints.csv` (kind, reachable / refused / gated). If a whole kind is refused from this machine (epa.gov and DataCite refused the Linux shell before), mark its rows `refused` and move on.

## S1: harvest (script)

Fetch each row's records (cap 6 requests per row, 400 in all). Save each raw response under `reads/<id>/` (JSON or XML as returned; HTML pages are not saved here). Log every request in `s1-requests.csv` (id, url, status, bytes, ms).

## S2: parse (script plus hand check)

For each row, write one packet `packets/<id>.json`:

```json
{"id": "...", "schema_source": "<record URL>", "route": "<S0 kind>",
 "columns": [{"name": "...", "type": "...", "meaning": "<description from the record, or empty>"}],
 "place_key": {"column": "...", "system": "...", "level": "<unit-vocabulary term>", "vintage": "<year or empty>", "basis": "<field name | field alias | description text | record title>"},
 "geometry": {"kind": "embedded | reference | none", "type": "...", "crs": "...", "reference": "<geography and vintage it must join to>"},
 "years_found": "...", "row_count": null,
 "not_read": ["sample_rows", "value_coding", "missing_coding"],
 "evidence": ["<record URL>"], "notes": "..."}
```

- Key system and level: reuse `run-p6-placekey/k0.py` vocabulary; levels from `unit-vocabulary.csv` only.
- **Vintage** only from evidence: a column name (`GEOID20`, `LSOA21CD`, `ZCTA5CE10`), a field alias or description, or the record text ("2020 census tracts"). Otherwise leave it empty and say so; never infer it from the data year.
- If the record lists several layers or files, take the one the row's `access_url` names; list the others in `notes`.
- Write `s2-summary.csv` (id, route, n_columns, key_column, system, level, vintage, vintage_basis, geometry_kind, crs, years_found, status = `schema` / `partial` / `no_schema` / `gated` / `refused`).
- **Hand check:** pick 10 packets at random; open the record and confirm key column, system and vintage. Report agreement (x of 10) and fix the parser if fewer than 8 agree, then re-run S2 once.
- Compare each packet with the row's page-verified `join_key_confirmed`, `finest_unit_confirmed` and `temporal_confirmed`; disagreements go to `contradictions.csv` (id, field, inventory value, metadata value, evidence).

## S3: agent reads (cap 20 rows)

For rows with `no_schema` or `partial` (WG-request rows first, then Gold), read the data dictionary, codebook or documentation page with WebFetch: the landing page plus at most two linked pages (an HTML or PDF data dictionary is fine; never a data file). Fill the same packet fields from what the page states, with `route = page` and the page URL as evidence. Rows still without a schema stay `no_schema`, with what was looked for in `notes`. Write `blocked.csv` for challenge pages, 401/403/429 and empty JS shells (don't work around them).

## S4: merge and record (always runs)

1. **Columns:** if the master has no `place_key_system`, `place_key_vintage`, `schema_source` or `schema_checked_on` columns, add them (empty) with a small script, writing `inventory-combined-<today>-p7a.csv` (no other change; confirm with a row-by-row diff that only those columns were added).
2. **Records:** write `records.jsonl`, one per packet with status `schema` or `partial`, setting only `place_key_system`, `place_key_vintage`, `schema_source`, `schema_checked_on`, and the existing columns `columns_found` (semicolon list, first 40), `place_key_found` (column name), `geometry_found`, `crs`, `years_found` where they were empty. `ev` = the record URL; `note` = route and status. Don't set `file_verified` or `verification_level` (no file was opened). Apply with `python scripts/apply_records_2026_11_02.py <p7a> inventory-combined-<today>-p7b.csv ../run-p7-schema/records` from `docs/discovery`. **Expect zero tier moves**; if any row moves, stop, set the master aside in `_to_delete/`, and report.
3. **Numbers check** on every count in the report, recomputed from `s2-summary.csv` and the new master.
4. **Report** `run-p7-schema/report.md`, answering with numbers:
   1. How many of the 85 got a schema, by route; requests and minutes per row; cost compared with #22 and #23.
   2. Key systems, levels and vintages found; how many rows now state a vintage (compared with 4% before); which crosswalks the vintages imply (2010 vs 2020 tracts, ZCTA 2010 vs 2020, LSOA 2011 vs 2021, NUTS versions).
   3. Contradictions with page-verified values, by field (contrary evidence first, as questions for Robert).
   4. **Is metadata enough?** For the six drafts in `publish/catalog-drafts-2026-11-03/` and up to 10 more rows, which recipe fields (from the drafts' structure) the packet fills and which still need a file read. Verdict: metadata-first is enough / enough with a file-read rung for N fields / not enough.
   5. A shortlist of up to 10 rows ready to try in the #44 recipe profile, with why.
5. **Docs:** the next iteration row in `iterations/README.md` and the `IT` list in `scripts/build_publish_package.py`; TODO 2.16 and 3.11 marked with the date and result; `docs/discovery/README.md` "Start here" counts and master name. Point `INV_ALL`/`ASOF` in the publish builder at the new master but **don't** build or publish; Robert batches PRs.

## Resume prompt

"Resume PROMPT-7 from `run-p7-schema/checkpoint.jsonl`: skip completed phases and rows, continue the current phase within its cap, then run S4."
