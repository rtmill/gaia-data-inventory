---
name: inventory
description: Contributor mode for the Gaia data inventory. Use when the user types /inventory (alone, with a claim issue number, or with a description like "20 candidates in Africa"), says "inventory: start", names a dataset to check or add, or wants to take work from the queue.
---

# Inventory contributor mode

You help one person decide **how much work to take**, do it, and leave **one ledger file**. You never edit the inventory itself: CI rebuilds it from the ledger after merge. Work from the repo root.

## 1. Start: show the queue, let the user carve

1. If you don't know the user's GitHub handle, ask (it goes in `by` and the file name). Then, without asking, get current: if the folder is on `main`, `git pull --ff-only`. If it is on a leftover `work/…` branch with nothing uncommitted, `git switch main` first; if there is an unsubmitted ledger file from an earlier session, say so and ask whether to submit or discard it before starting anything new. **Don't create a branch now**: the work is only a new file under `ledger/`, and the branch is made when submitting (section 6). The user never handles branches.
2. **`/inventory <issue number>`**: the user already has a claim. `python scripts/queue.py --issue <n>` lists its items; go to section 3.
3. **Otherwise** run `python scripts/queue.py` (read all of its output; don't truncate it) and present it in this order. Plain words throughout; no `basis` text unless asked.
   - **Open with two or three sentences of grounding** before any numbers, in your own words: this is the working group's shared list of public place-based datasets for health research; each dataset has to be found and then checked (licence, years, geography, access) before Gaia can use it; the work is cut into small pieces so many people can chip away at it; in this session they pick a piece, you do the reading, and they approve what gets submitted. Skip this for someone who has clearly done it before.
   - **Where things stand**, introduced as such: the stages, each explained in a few words the first time (a lead is something that might be a dataset; listed means it's in the inventory but unchecked; verified means its licence, years, geography and access were confirmed; fully specified means its columns, place key and geometry are recorded, which is what a loading recipe is written from), with the count at each.
   - **One sentence that says what the table is:** each row is a kind of work they can take on, in the order a dataset moves through the stages.
   - **The table**, in the script's order, `explore` included as an ordinary row: **Work** (a plain label, with the script's name in brackets, e.g. "Check an unverified dataset (read)") | **What it does** (from which stage to which) | **What you end up with** | **How much is open** (count, and the token cost of all of it) | **Tokens per item** (say "measured" or "a guess" exactly as the script does) | **What 10 items typically gives** (keep the script's caveats, such as "a guess" or "expect fewer"). Minutes are Claude's working time, not the person's: mention them once under the table, not as a column.
   - **A suggestion only if the script prints "maintainers suggest this now"** for a row; quote its reason. Otherwise don't recommend one: say it depends on whether they'd rather grow the list, firm up what's there, or get datasets ready for Gaia, and that they can also choose by topic or region.
   - **Then ask, in these words or close to them:** "Which would you like to take on, and how much of it? If you don't mind, I'll start with the default: 10 items. Or give me a number of items, a time limit, or a token limit." Add one line: they can narrow any row by topic, region or publisher, or name a dataset they already know.
   Do **not** list the approaches here. Only if the user picks `explore`, go to section 1b.
4. Offer slices if they want to narrow it: `python scripts/queue.py --by region --kind candidate` (also `category`, `host`, `publisher`, `tier`). Filters: `--region`, `--category`, `--host`, `--publisher`, `--tier`, `--match <title text>`, `--wg` (working-group requests), `--fresh` (never touched). Same-host items are cheaper together (one site, one licence page), so a `--host` slice is a good default suggestion for `read` and `settle`.
5. Show what they'd get: `python scripts/queue.py --kind <k> [filters] --n <N>`. When they agree, claim it by adding `--claim`: this opens an issue assigned to them, and takes those items out of everyone else's view. Note the issue number.
6. **"A dataset I know"** needs no claim: go straight to packet a.
7. Note the start time. Don't read the big CSVs; use `queue.py` and `lookup.py`.

Kinds and packets: `read`, `settle`, `successor` = packet b; `schema` = c; `person-read` = d; `candidate` = e; a dataset the user names = a.

## 1b. Explore: continue an approach, or design one

1. Run `python scripts/queue.py --approaches` and show its rows as one table: **Approach** | **How it did last time** | **Verdict** | **What's left**. Add a last row: **"Something new"**: work out a new way of finding data together. Ask which, and the budget if not given yet.
2. **Continuing one:** `python scripts/queue.py --approach "<name>"` gives the full row. Read its brief (the `continue` path) and the same folder's `results.md` (what happened last time and what to change). Start from "what's left"; don't re-run what was done.
3. **Something new:** ask what they have in mind (a source, a kind of data, a place, a search trick). Run `python scripts/queue.py --approaches --all` to check it isn't a variant of something tried or closed, and say so if it is. Then write a short brief with them before doing anything: the question the run answers, where it will look, what counts as a hit, the caps, and what result would mean "worth scaling". Save it as the first part of the run's note (step 6).
4. Size the run to the budget and say so before starting: how many searches or listings, how many records read (use the approach's cost line where there is one), and a hard stop. Rules for every run: one job, no sub-agents, metadata and pages only (no data files), no sign-ins or bot-check workarounds, 1 request per second per host.
5. Claim it: check that no open `claim` issue names the same approach, then `gh issue create --label claim --assignee @me --title "[claim] explore: <name> (<handle>)" --body "<what you will do and the caps>"`.
6. Outputs, all under `ledger/` so they merge automatically:
   - **Leads you found but didn't read:** `ledger/leads/<YYYY-MM-DD>-<handle>-<slug>.csv` with columns `ref` (DOI or landing URL), `title`, `publisher`, `year`, `anchor` (from `method/anchors.csv`), `region`. Check each with `python scripts/lookup.py` first and leave out what's already in. They join the queue as `candidate` items after merge.
   - **Datasets you read:** new-row records in the session's ledger file, as in section 5 (packet e).
   - **What happened:** `ledger/notes/<YYYY-MM-DD>-<handle>-<slug>.md`: the brief (for a new approach), what you searched, counts (found, already known, new, read, added), precision if you can measure it, what blocked, and your verdict (scale, scale with changes, or drop, and why). A maintainer folds this into `method/approaches.csv`, which is how the next person sees how the approach is doing.
7. The session's `meta` line uses `"kind": "explore: <name>"`. Then finish as in section 6.

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

1. `git fetch origin`, then `python scripts/validate.py ledger/<your file>.jsonl --against origin/main`. Fix every error. If it says a row was changed on main since you started, run `git pull --ff-only`, then `lookup.py --id` for that row, and reconsider your record.
2. Tell the user in 3-5 lines: items done against items claimed, checks settled, rows added, candidates ruled out, what was blocked, anything that looked wrong in an existing row, and what the session took against the estimate.
3. Ask one question: **"Submit this?"** On yes, do all of it yourself, in this order: `git switch -c work/<handle>-<YYYYMMDD-HHMM>` (the new file comes along), `git add ledger/`, `git commit -m "Inventory: <kind> (<n> items)"`, `git push -u origin HEAD`, `gh pr create --title "Inventory: <kind>, <n> items" --body "Closes #<claim issue>. <your summary>"`, and finally `git switch main` so the folder is left where it started. No AI attribution lines anywhere. Tell the user the PR link and that GitHub will check it and merge it by itself within a few minutes if it passes; nothing more is needed from them.
4. If the user comes back saying the check failed: `gh pr checks`, read the failing log (`gh run view --log-failed`), `git switch` to that PR's branch, fix the ledger file, commit, push, and `git switch main` again.
