# Place-key search, Canadian DGUID (2026-11-18, rtmill, claim #40)

**Approach:** continue "Place-key search" (method/iterations/23-place-key-spike). The brief's "next" step is to read the 33 unread keyed datasets, but the list (`k2-hits-classified.csv`) is not in this repository, so this run did the fallback: 2 searches for one key system the approach has not tried (Canadian DGUID). Metadata only (6 requests in all, including re-runs of search 1 for detail); no data files; 1 request per second.

**Question:** do searches on the code name DGUID find keyed datasets that topic searches missed?
**Hit means:** a reusable dataset whose rows are places keyed by DGUID, not in the inventory.
**Caps:** 2 searches, up to 20 hits each, at most 3 records read. **Worth scaling if:** at least 5 new keyed datasets per search.

## Searches
| # | Where | Query | Hits |
|---|---|---|---|
| 1 | open.canada.ca CKAN `package_search` | `DGUID`, newest first | 2 |
| 2 | Zenodo `/api/records` | `DGUID`, most recent | 0 |

## Counts
Found 2, already known 2 (both are editions of the family `ca_statcan_census_boundary_files_2021`: the 2026 edition, CKAN id edf21f3a-33c2-4602-9694-d6e1361692a9, created 2026-11-18, scores 0.96 against the 2021 row; the 2021 edition is the row itself), new 0, read 1 (CKAN package record of the 2026 edition: Open Government Licence - Canada, ESRI REST and WMS resources, DGUID linked to the 2026 Dissemination Geographies Relationship File), added 0. No leads file: nothing new to list. Precision: 2 of 2 hits were boundary files, not keyed datasets (0 of 2).

## What blocked
Nothing was blocked. Bare code searches return almost nothing (2 and 0 hits), the same weakness that results.md recorded for GEOID: the code name is not what catalog text says. Rephrasings ("dissemination area", "census tract Canada", "Statistique Canada" + health topic) were not tried because the claim capped the run at 2 searches.

## Side finding
The 2026 Census Boundary Files edition is a new vintage of a family already in. It may need a vintage note on the existing row; it is not a new row (one row per family).

## Verdict
**Drop the bare-code form for DGUID; scale with changes** only as phrase searches ("dissemination area", "Statistics Canada census profile") on CKAN. The yield of this run does not support scaling the code-name search.
