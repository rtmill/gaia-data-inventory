# P7: schema and place-key pass over the recipe-ready queue (TODO 2.16 first rung; feeds 3.11), report 2026-11-18

> **This assumes:** (1) a machine-readable record (CKAN, Zenodo, Dataverse, ArcGIS, OpenFEMA, Census `variables.json`, STAC, a data.gouv.fr API record) or, failing that, a documentation page, states a dataset's columns and place key well enough to start a recipe; (2) the target set is the 85-row `queues/recipe-ready.csv` (licence, access, join key and format all `pass`), read against master `inventory-combined-2026-11-03-p6e.csv`; (3) metadata only: no sample rows, no value coding, no data files opened (Robert, 2026-11-18). The cap on page reads (20 rows) is mine to set per the prompt, not a finding.

## Check these first (contrary evidence, as questions for Robert)

1. **Most of the 85 rows have no machine-readable record to read.** S0 could derive a record route from the row for only 26 of 85 (25 usable, 1 gated); 59 had to go to a documentation page or stay unread. Only 7 of the 25 routed rows returned a column list (ArcGIS 1, Census 1, CKAN datastore 3, OpenFEMA 1, data.gouv.fr description table 1). Is "metadata first" the right first rung when 70% of the queue has no API record? (The queue is Gold and Silver rows read on landing pages, so this may be a property of the queue, not of the metadata approach.)
2. **The page reads mostly re-found what the page-verification pass already recorded.** I compared 13 of the 20 page-read rows with their stored `join_key_confirmed` and `temporal_confirmed`; for most of them the key, unit and vintage were already stated. What was new: column lists for GHCN, the Census gazetteer and urban/rural block file, the ABS DataPack key pattern `STE_CODE_2016`, and the CBS 2024 erratum. The page rung's value was mostly in making already-known facts structured (system, level, vintage, columns), not in new facts.
3. **The packets are hand-coded per row, not parser output.** The prompt says "script plus hand check". `s2.py` contains one handler per record shape and per-row text for the narrative fields; I read each record before writing its handler. The hand check below (10 of 10) therefore measures my reading of the records, not a reusable parser. A generic parser exists only for the columns of ArcGIS, CKAN datastore, OpenFEMA and Census records.
4. **Two packet values are judgement calls, not evidence:** Venezuela facilities level `point` (the record says "location of hazardous facilities"), and the French commune code `code_insee` filed under `LAU` (the vocabulary has no INSEE term; the inventory says `admin3`).
5. **`ev` in the apply script has side effects.** With `ev` set, `apply_records_2026_11_02.py` also appends the URL to `partB_pages_read` and `partB_source` and sets `verified_on` to 2026-11-18 on all 35 rows. A schema read is not a page verification, so `verified_on` now overstates what was verified on those rows. `verification_level` and `file_verified` were not touched. Do you want those three columns restored for the 35 rows, or the apply script changed to leave them alone for schema records?
6. **catalog.data.gov's CKAN API returned 404 for both `package_show` and `package_search`** on 2026-11-18, so HUD QCT/DDA and NAIP are `refused`. Either the API moved or this machine is blocked; I did not work around it.
7. **CalEnviroScreen's record says "License not specified"** (rights: "No restrictions on public use"). The inventory row passes licence; the evidence is the rights statement.

## Numbers

All counts below are recomputed by `numbers_check.py` (output in `numbers-check.txt`).

| Phase | Result |
|---|---|
| S0 | 85 targets: record route for 25 (CKAN 10, repo API 6, Dataverse 3, ArcGIS 3, STAC 1, Zenodo 1, Census 1), gated 1 (AHRQ on openICPSR), none 59. Endpoints: 7 kinds tested, all reachable (`endpoints.csv`). Census `variables.json` and `geography.json` need no key |
| S1 | 25 rows, 34 requests (28 HTTP 200, 6 HTTP 404: 4 data.gov and 2 datastore), 40 s of request time. 13 CKAN, 2 follow-ups for datastore fields, 1 ArcGIS follow-up for the service layer |
| S2 | 85 packets; hand check 10 of 10 |
| S3 | 20 rows read, 27 requests (23 HTTP 200, 403 ×2, 404 ×1, 202 ×1); `blocked.csv` lists 3 rows |
| S4 | `inventory-combined-2026-11-18-p7b.csv`, 805 rows, 35 rows carry a schema record, **0 tier moves** |

**Final status of the 85 rows:** `schema` 12 (column list found), `partial` 23 (key, geometry or years found, no column list), `no_schema` 45, `refused` 5 (gov.scot HTTP 202 empty body, AHRQ 403, Smithsonian 403, data.gov API 404 ×2).

## Question 1: how many got a schema, by route, and what it cost

| Route | Rows | schema | partial | no_schema / refused |
|---|---|---|---|---|
| CKAN (HDX, Mekong, open.canada, Bogota, data.ca.gov) | 8 | 3 | 5 | 0 |
| Repository / publisher API (OpenFEMA, data.gouv.fr, EEA GeoNetwork, geoBoundaries, WorldPop ×2) | 6 | 2 | 4 | 0 |
| Dataverse (CIESIN ×3) | 3 | 0 | 3 | 0 |
| ArcGIS (Miami Hub layer; BTS and EIA portals) | 3 | 1 | 0 | 2 |
| Census API | 1 | 1 | 0 | 0 |
| Zenodo, STAC | 2 | 0 | 2 | 0 |
| Page read (S3) | 20 | 5 | 9 | 6 (3 no_schema + 3 refused) |
| No route, unread (S3 cap) | 40 | 0 | 0 | 40 |
| Refused (data.gov) | 2 | 0 | 0 | 2 |
| **Total** | **85** | **12** | **23** | **50** |

- **Cost:** 68 requests (7 endpoint tests, 34 in S1, 27 in S3) for 85 rows, so 0.8 per row overall, 4.3 per row that got a column list (16 rows have one: the 12 `schema` rows plus 4 `partial` rows whose "columns" are paraphrases or examples: Zenodo, the DLR band, Microsoft and the ABS DataPack headings). Against #22 (about 260 requests for 32 rows, about 8 per row) and #23 (about 65 for 20 rows, about 3 per row). **No wall-clock was measured** (same position as #22 and #23), so no minutes-per-row figure is claimed; the S1 requests took 40 s in total.
- **What a schema record gave** (35 packets): geometry kind 35, key system and level 24, key column named 18, column list 16, years 23, vintage 10, CRS 8. Types and meanings exist for 11 packets, and types from a platform (CKAN datastore, ArcGIS) are inferred by that platform.
- **A concrete recipe hazard found:** CalEnviroScreen's datastore types `Census Tract` and `ZIP` as numeric, so a recipe on the XLSX has to pad the tract to 11 digits (California FIPS starts with 06).

## Question 2: key systems, levels, vintages, crosswalks

- **Systems named in the 35 packets:** grid 6, GEOID/FIPS 6, national statistical code 3 (Statbel sector, INSEE IRIS, SCB DeSO), coordinates 3, non-geographic ID 2 (Miami COMDISTID, GHCN station ID), and one each for ASGS, ZIP code (EU postcode), OCHA P-code, StatCan DGUID, LAU (INSEE commune), geoBoundaries, embedded geometry; 8 with no system (INE sections, Microsoft footprints, Venezuela facilities, EEA E-PRTR, Bogota, CIESIN ×3).
- **Levels:** point 6, small_area 5, raster 5, tract 3, block 2, polygon 2, and one each of postcode, grid_100m, lau, country, county; 7 empty.
- **Vintage stated:** 10 packets (**11.8% of the 85**) have a `place_key_vintage`: USALEEP 2010 (tract), PL 94-171 2020 (API `geography.json` `referenceDate`), urban/rural blocks 2020, ABS DataPacks 2016 (from the column name `STE_CODE_2016`), StatCan 2021, Statbel 2023, Eurostat postal codes 2024 (file edition; 2020 also offered), INSEE IRIS 2025-01-01, SCB DeSO 2025, Ethiopia P-codes 2024. **Compared with the 4% for all Gold/Silver rows** (#23), the base is different (85 recipe-ready rows, not 604) and on this same queue the P6 regex had found 8 of 85 (9.4%). The P7 packets add 7 rows not found before; the union is 15 of 85 (17.6%). One conflict: P6 recorded 2021 for the Eurostat postal-code row, the page offers editions 2024 and 2020 (`contradictions.csv`).
- **Crosswalks the vintages imply:**
  - US tracts: USALEEP is on **2010** tracts while the Census block file and PL 94-171 are 2020, so USALEEP to a 2020-tract product needs the 2010 to 2020 tract crosswalk. CalEnviroScreen's tract vintage is not in its record.
  - Sweden: DeSO **2018 and 2025** coexist; statistics before 2025 are not recomputed on DeSO 2025 (SCB page), so mixing years needs a DeSO crosswalk.
  - Australia: ASGS **2016** DataPacks and 2021 packs (code column carries the year).
  - France: INSEE IRIS 2023 data on the **1 January 2025** geography; the radon/commune table states no commune vintage (mergers change the code set).
  - Belgium: statistical sectors 1 January 2023 on 2022 municipality boundaries; Spain: one national section file per year 2001 to 2025 (no stable edition); EU postal codes: NUTS version of the NUTS code not stated.
  - No UK LSOA or NUTS-version evidence in this queue (none of the queue's UK rows had a route).

## Question 3: contradictions with page-verified values (`contradictions.csv`, 12 rows)

By field: `join_key_confirmed` 5, `temporal_confirmed` 4, `finest_unit_confirmed` 2, key vintage 1. Real conflicts, as questions:

1. **WorldPop 100 m and 1 km:** the inventory says each year 2015 to 2030 (R2025A) with 2000 to 2020 archived; the REST listing shows `popyear` 2000 to 2020 only. Is the REST alias (`wpgp` is named in the row; `wpic1km` is mine) the older Global1 collection, and is the release the inventory cites reachable only through another route?
2. **CBS 100 m grid:** the page carries an erratum that the 2024 data (published 2026-07-09) dropped records through a failed join, corrected 2026-08-28. The inventory says 2023 and 2024 were "supplemented in Aug 2026". Should the row say the 2024 data had an error until 2026-08-28?
3. **data.gouv.fr radon table:** inventory page read says last updated 21 October 2026; the record says the resource was modified 2026-11-16 (auto-refreshed). Unit term: inventory `admin3`, packet `lau`; which term should the vocabulary use for a French commune?
4. **Ethiopia market centres:** the inventory key is "geometry (shapefile)"; the record says OCHA 2024 pcodes and woredas were added, so a P-code key exists.
5. **Silences, not contradictions:** the EEA E-PRTR record names no key; the PL 94-171 API has no `GEOID` variable (FIPS `for`/`in` clause) where the bulk files have one; the Bogota record says the unit is a city block (manzana) and the inventory says polygon.

## Question 4: is metadata enough?

**The six drafts in `publish/catalog-drafts-2026-11-03/` are not among the 85 rows** (EJI, TRI, AQS, COI, UCMR 5 and the PWS service areas are not in the recipe-ready queue), so no packet was compared field by field with a draft. What follows compares packets with the drafts' *structure* (`gaia:recipe`: `data_source`, `geom_spec`, `geom_dependency`, `variables[]` with `attr_spec`, `geom_join`) and with the drafts' own `open_questions`.

`metadata-enough.csv` marks, for the 35 packets with anything, which recipe inputs the metadata filled:

| Recipe input | Packets (of 35) |
|---|---|
| Geometry kind (embedded, reference, none) | 35 |
| Key system and level | 24 |
| Years | 23 |
| Key column named | 18 |
| Column list | 16 |
| Column types or meanings | 11 |
| Key vintage | 10 |
| CRS | 8 |
| Missing-value codes, archive file names, sample rows | 0 (not read by design) |

- **What metadata could not fill, from the drafts' own findings:** `DISTINCT` and the facility-by-chemical shape (rows), per-row datum, non-detect qualifiers and missing-value codes, import-time renames (`ogr_sql`), and dates when the file has none. These are 6 of the 12 recipe inputs I count in the drafts' structure (my count, not the drafts'): file name in an archive, `ogr_sql`, `where`, qualifier and missing codes, date source, per-row datum. The other 6 (URL, format, geometry columns, variables, key and dependency, join) are filled for a minority of rows.
- **Platform-inferred types are not reliable:** CalEnviroScreen's datastore types Asthma, Poverty and Education percentiles as `text` and Census Tract as `numeric`.
- **Verdict: enough with a file-read rung for 6 of 12 recipe inputs, and not enough as the only rung for the queue as a whole:** 16 of 85 rows (19%) have a column list after both rungs, and 40 rows have no machine-readable route and were not read. For the rows that do have a record, the metadata rung is good value (about 4 requests per row with a column list, no downloads). The next rung needs a small partial read of the file's header and first rows, and a page-read rung for rows where the dictionary sits in an xlsx (Statbel, INSEE, ABS Metadata), which this pass did not open.

## Shortlist: up to 10 rows to try in the #44 recipe profile

Chosen for a named key column, a system and level, columns listed, and no geometry download needed to start.

| Row | Why |
|---|---|
| `us_cdc_usaleep` | Tract ID plus STATE2KX/CNTY2KX/TRACT2KX; vintage 2010 stated; the crosswalk case (2010 vs 2020) |
| `us_census_urban_rural` | GEOID 15-digit block, 2020, full field list; digit-leading column names (`2020_POP`) test quoting |
| `us_census_gazetteer` | GEOID plus INTPTLAT/INTPTLONG, nine fields; gives a point geometry from the file itself; vintage varies by yearly file |
| `us_census_decennial_pl94171` | 338 variables from the API, vintage 2020 from `referenceDate`; a variable-family test (one recipe, many variables) |
| `us_fema_openfema_disaster_declarations` | 29 typed fields, state and county FIPS, no geometry (needs a county boundary dependency); `fipsCountyCode` '000' means statewide |
| `us_ca_oehha_calenviroscreen` | Tract in a numeric field, so the padding rule is testable; licence caution above |
| `mekong_odm_health_facilities_in_thailand_2020` | Lat/Long fields, CC BY, point geometry from columns (the TRI-style case) |
| `fr_datagouv_qualit_de_l_air_de_l_eau_et_potentiel_radon_par_commune` | 13 columns with descriptions, INSEE commune code, one CSV; commune vintage unstated; hosted by a third party |
| `us_com_comission_districts` | Feature layer with its own polygons (EPSG:3857 service); a no-key, embedded-geometry case |
| `global_noaa_ghcn_daily` | Fixed-width station and daily files; station ID joins the stations file (the non-geographic-ID case) |

## Files

`s0.py`, `s0-routes.csv`, `endpoints.csv`, `s1.py`, `s1b.py`, `s1-requests.csv`, `reads/`, `s2.py`, `packets/` (85), `s2-summary.csv`, `s3.py`, `page.py`, `s3-requests.csv`, `blocked.csv`, `contradictions.csv`, `s4a.py`, `s4b.py`, `records.jsonl` (35), `records-tier-moves.csv` (0 moves), `numbers_check.py`, `numbers-check.txt`, `metadata-enough.csv`, `checkpoint.jsonl`, `lib.py`, this report. Masters: `inventory-combined-2026-11-18-p7a.csv` (four empty columns added: `place_key_system`, `place_key_vintage`, `schema_source`, `schema_checked_on`; no other change, confirmed row by row), `inventory-combined-2026-11-18-p7b.csv` (35 rows with a schema record). A failed first write of p7a (read back before the file was closed) is in `_to_delete/inventory-combined-2026-11-18-p7a.partial.csv`.

## Not done

- **Unread rows:** 40 rows with no machine-readable route were not read (S3 cap 20). Among the 20 read, rows with a partial status whose page cannot give more (rasters, HDX) were skipped in favour of Gold rows without a schema, so the order is not strictly the queue's.
- **Dictionaries in data files not opened:** Statbel `Columns description_0.xlsx`, INSEE dictionary workbook, ABS Metadata xlsx.
- **Docs not built or published:** the publish builder now points at the new master; `build_publish_package.py` was not run.

## Follow-up (2026-11-18, Robert)

- **Check 5 resolved:** `verified_on`, `partB_pages_read` and `partB_source` restored from p6e for the 35 rows (105 cells) in `inventory-combined-2026-11-18-p7c.csv`; `schema_source` keeps the record URL. The apply scripts (`scripts/apply_records_2026_11_02.py`, `onramp/method/scripts/apply_records.py`) no longer stamp those columns for records that set `schema_source`, or that carry `"verifies": false`. p7c is the current master; tiers unchanged.
- **S3 not resumed** for the 40 unread rows: the verdict stands, and those rows are better served by the file-read rung.
