---
name: inventory
description: Contributor mode for the Gaia data inventory. Use when the user types /inventory (alone, with a claim issue number, or with a description like "20 candidates in Africa"), says "inventory: start", names a dataset to check or add, or wants to take work from the queue. Also use when the user says "wrap up", "finish now" or "stop here" during inventory work, returns to an unfinished session, or asks where their inventory work stands ("/inventory status", "where was I").
---

# Inventory contributor mode

You help one person decide **how much work to take**, do it, and leave **one ledger file**. You never edit the inventory itself: CI rebuilds it from the ledger after merge. Work from the repo root.

## 1. Start: show the queue, let the user carve

0. **First, every session:** `python scripts/preflight.py`. If it lists anything to do, stop there: show the user its numbered steps exactly as printed (they are written for the user to follow), tell them to do them in a normal terminal and then type `/inventory` again. Don't try to work around a missing or signed-out GitHub CLI, don't install anything yourself, and don't start work that can't be claimed or submitted. Signing in needs a browser, so it can't be automated.
1. If you don't know the user's GitHub handle, ask (it goes in `by` and the file name). Then, without asking, get current: if the folder is on `main`, `git pull --ff-only`. If it is on a leftover `work/…` branch with nothing uncommitted, `git switch main` first; if there is an unsubmitted ledger file from an earlier session (a `ledger/*.jsonl` that git shows as new or changed), an earlier session stopped before submitting: go to section 7 (recover) before anything else. **Don't create a branch now**: the work is only a new file under `ledger/`, and the branch is made when submitting (section 6). The user never handles branches.
2. **`/inventory <issue number>`**: the user already has a claim. `python scripts/queue.py --issue <n>` lists its items; go to section 3.
3. **Otherwise** run `python scripts/queue.py` (read all of its output; don't truncate it) and present it in this order. Plain words throughout; no `basis` text unless asked.
   - **Open with two or three sentences of grounding** before any numbers, in your own words: this is the working group's shared list of public place-based datasets for health research; each dataset has to be found and then checked (licence, years, geography, access) before Gaia can use it; it is crowdsourced, divide and conquer (say so in those words): there is far more than one person can do, so each contributor takes a share of whatever size suits them; in this session they choose what to work on and how much, you do the reading **on their Claude usage (the tokens it takes are their contribution, which is why each option shows its token cost)**, and they approve what gets submitted. (Nothing is pre-divided: don't say the work is "cut into pieces".) Skip this for someone who has clearly done it before.
   - **Where things stand**, introduced as such: the stages, each explained in a few words the first time (a lead is something that might be a dataset; listed means it's in the inventory but unchecked; verified means its licence, years, geography and access were confirmed; fully specified means its columns, place key and geometry are recorded; then a loading recipe is drafted from that; and the end point is the dataset in the Gaia catalog, where it can be loaded), with the count at each. Say plainly that the last two steps are the goal and that recipe drafting is not open yet (it waits for the recipe format), so today's work gets datasets ready for it.
   - **One sentence that says what the table is:** each row is a kind of work they can take on, in the order a dataset moves through the stages.
   - **The table**, in the script's order, with `explore` and "a dataset you have in mind" included as ordinary rows, and "draft a recipe" as the last row, marked not open yet: **Work** (a plain label, with the script's name in brackets, e.g. "Check an unverified dataset (read)") | **What it does** (from which stage to which) | **What you end up with** | **How much is open** (count, and the token cost of all of it) | **Tokens per item** (say "measured" or "a guess" exactly as the script does) | **What 10 items typically gives** (the script's "10 items" line, with its caveats such as "a guess" or "expect fewer"; never restate it per 30 minutes). Minutes are Claude's working time, not the person's: mention them once under the table, not as a column. For `explore`, put "depends on the approach" in the last two columns.
   - **A suggestion only if the script prints "maintainers suggest this now"** for a row; quote its reason. Otherwise don't recommend one: say it depends on whether they'd rather grow the list, firm up what's there, or get datasets ready for Gaia, and that they can also choose by topic or region.
   - **Then ask, in these words or close to them:** "Which would you like to take on, and how much of it? If you don't mind, I'll start with the default: 10 items. Or give me a number of items, a time limit, or a token limit." Add one line: they can narrow any row by topic, region or publisher.
   Do **not** list the approaches here. Only if the user picks `explore`, go to section 1b.
4. Offer slices if they want to narrow it: `python scripts/queue.py --by region --kind candidate` (also `category`, `host`, `publisher`, `tier`). Filters: `--region`, `--category`, `--host`, `--publisher`, `--tier`, `--match <title text>`, `--wg` (working-group requests), `--fresh` (never touched). Same-host items are cheaper together (one site, one licence page), so a `--host` slice is a good default suggestion for `read` and `settle`.
5. Show what they'd get: `python scripts/queue.py --kind <k> [filters] --n <N>`. When they agree, claim it by adding `--claim`: this opens an issue assigned to them, and takes those items out of everyone else's view. Note the issue number.
6. **A dataset the user has in mind** needs no claim: go to section 1c.
7. Note the start time. Don't read the big CSVs; use `queue.py` and `lookup.py`.

Kinds and packets: `read`, `settle`, `successor` = packet b; `schema` = c; `person-read` = d; `candidate` = e; a dataset the user names = a.

## 1b. Explore: continue an approach, or design one

1. Run `python scripts/queue.py --approaches` and show its rows as one table: **Approach** | **How it did last time** | **Verdict** | **What's left**. Add a last row: **"Something new"**: work out a new way of finding data together. Ask which, and the budget if not given yet.
2. **Continuing one:** `python scripts/queue.py --approach "<name>"` gives the full row. Read its brief (the `continue` path) and the same folder's `results.md` (what happened last time and what to change). Start from "what's left"; don't re-run what was done.
3. **Something new:** ask what they have in mind (a source, a kind of data, a place, a search trick). Run `python scripts/queue.py --approaches --all` (every approach, including closed ones) to check it isn't a variant of something tried or closed, and say so if it is. Then write a short brief with them before doing anything: the question the run answers, where it will look, what counts as a hit, the caps, and what result would mean "worth scaling". Save it as the first part of the run's note (step 6).
4. Size the run to the budget and say so before starting: how many searches or listings, how many records read (use the approach's cost line where there is one), and a hard stop. Rules for every run: one job, no sub-agents, metadata and pages only (no data files), no sign-ins or bot-check workarounds, 1 request per second per host.
5. Claim it: check that no open `claim` issue names the same approach, then `gh issue create --label claim --assignee @me --title "[claim] explore: <name> (<handle>)" --body "<what you will do and the caps>"`.
6. Outputs, all under `ledger/` so they merge automatically:
   - **Leads you found but didn't read:** `ledger/leads/<YYYY-MM-DD>-<handle>-<slug>.csv` with columns `ref` (DOI or landing URL), `title`, `publisher`, `year`, `anchor` (from `method/anchors.csv`), `region`. Check each with `python scripts/lookup.py` first and leave out what's already in. They join the queue as `candidate` items after merge.
   - **Datasets you read:** new-row records in the session's ledger file, as in section 5 (packet e).
   - **What happened:** `ledger/notes/<YYYY-MM-DD>-<handle>-<slug>.md`: the brief (for a new approach), what you searched, counts (found, already known, new, read, added), precision if you can measure it, what blocked, and your verdict (scale, scale with changes, or drop, and why). A maintainer folds this into `method/approaches.csv`, which is how the next person sees how the approach is doing.
7. The session's `meta` line uses `"kind": "explore: <name>"`. Then finish as in section 6. A run that finds nothing is still worth submitting: write the note (what was searched and why it came up empty) and the session file with `items` 0; skip the leads file.

**What you may write on the user's computer:** only inside this repository folder, and only these: the session's file under `ledger/` (and `ledger/packets/`, `ledger/leads/`, `ledger/notes/` for the kinds that use them), and `.inventory-discarded/` when the user discards work. Don't save fetched pages, downloads, logs or scratch files anywhere, inside or outside the folder, temporary directories included. If you need something from a page again, work from what you already read, or leave the check open.

## 1c. A dataset the user has in mind

They may give a name, a web address or DOI, or both. Nothing is reserved for this.

1. **Find it, cheaply.** With an address or DOI: fetch that one page or record. With only a name: `python scripts/lookup.py "<name>"` first, then at most one web search to find the publisher's own page (not an aggregator's copy).
2. **Confirm before doing the work.** As soon as you can say what you found, stop and show it in a few lines: the title as the publisher gives it, the publisher, the address, what it covers (years, geography) if the first page says, and anything that makes it ambiguous (several versions or editions, a family of related products, a mirror on another site, a similarly named dataset from someone else). Ask: "Is this the one you mean?" If there are two or three plausible matches, list them and ask which. Don't read further pages or write any record until they confirm.
3. **Say whether it's already in.** Show the `lookup.py` matches (inventory rows and leads). If it is in: show its tier and open checks, and offer to settle those instead of adding anything. If a version or sibling is in: ask whether theirs is a new entry or belongs with that one (one entry per product family).
4. **Then do it** as packet a (section 3 limits, section 5 record), or as an update to the existing row. If it is already in and its page is blocked, write nothing: say so, and offer it as a page for the user to open themselves. If the user knows things about the dataset, treat that as a pointer to where to look, not as evidence: every value still needs its link.

## 2. Finding things

- `python scripts/lookup.py "<name, DOI, URL or id>"`: best matches in the inventory and the candidate families. **Before proposing any new row**, check here: a score of 0.75 or more with the same publisher, or the same DOI root, means it's already in. Update that row instead.
- `python scripts/lookup.py --id <id>`: the key fields of one row, including its notes (read them before re-checking it). Add `--all` only when you need a check's detail or evidence.

## 3. Limits per item (the user chose how many items; these bound each one)

| Packet | Fetches per item | Stop the item when |
|---|---|---|
| a | 4 | drafted, or blocked |
| b (`read`, `settle`) | 3 | checks settled, or blocked |
| b (`successor`) | 5 (the dead address, one search, the new page, up to two of its pages) | a new address with its checks, or confirmed gone |
| c | 6 (metadata records first, then one documentation page) | packet filled, or a data file would be needed |
| d | 0 | the user has reported the page |
| e | 4 per family | a row or a verdict |

Stop the session at the user's budget (items, time or tokens), whichever comes first; write up what's done. Unfinished items go back to the queue when the claim closes. Per item: the landing page or repository record first, then at most two more pages. The publisher's own licence or terms page on the same site may be one of them even when the dataset page doesn't link to it (a site-wide terms page settles the licence as `warn`, not `pass`). If the cap is reached with a check still open, leave it open and say so in the note; don't go over. Web search only to find a moved page's successor (`successor` items), and say so in the note.

**Records before pages.** These answer in one call and count as a read: Zenodo `/api/records/<id>` (check `access_right`: closed or restricted is `restricted`), figshare `/v2/articles/<id>`, Dataverse `/api/datasets/:persistentId/?persistentId=doi:<DOI as published>`, CKAN `/api/3/action/package_show?id=…` (and `datastore_search?resource_id=…&limit=0` for fields), Socrata `/api/views/<id>.json`, ArcGIS layer `?f=json`, Census `variables.json`, STAC collection JSON, FGDC or ISO XML metadata. A DataCite record alone does not settle a licence and gives publication years, not coverage.

**Blocked** (challenge page, 401/403/429, "enable JavaScript", empty shell; ICPSR, openICPSR and NaNDA always are): never work around it. Still write a record, so the item isn't offered to the next person: `{"id": …, "by": …, "packet": …, "blocked": true, "ev": "<the address that blocked>", "note": "blocked: <what you got>", "set": {}}`. For a `read` item only, put `"url_health": "blocked"` in `set`, which moves it to the pages a person opens. For `settle`, `schema` and `successor` items leave `set` empty (a blocked `schema` record needs no packet file). Tell the user at the end which were blocked.

**Garbled text** from a metadata file usually means it isn't UTF-8 (older government metadata is often UTF-16): decode what you already have before fetching again. A re-fetch counts against the cap.

## 4. Judging the checks

Full definitions: `method/BRIEF-page-reads.md` ("The checks"). Values: `pass`, `warn`, `fail`, `n.a.`, `not_checked`. Every check you set gets `<check>_detail` (what you read, a few words) and `<check>_evidence` (the URL), **except `chk_link_live` and `chk_withdrawn`, which have only `_detail`** (their evidence is the record's `ev`). Leave what you didn't read alone. **If you read the page and nothing more can be settled, say so in the note and set only `chk_link_live`; don't restate checks you didn't re-read.** A dataset is offered once per kind of work, so it won't come back to the queue.

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

One file per session: `ledger/<YYYY-MM-DD>-<handle>-<slug>-<HHMM>.jsonl`, where the slug is lowercase (e.g. `candidate-africa`) and `<HHMM>` is the time you start, so two sessions on one day never pick the same name. One JSON object per line. If a file of that name already exists, on disk or on GitHub, pick another time suffix; never overwrite or rename someone's file.

**Save as you go.** Create the file with its `meta` line as soon as work is claimed (put the claim number in it; `items` 0 for now). **Append each item's record to the file the moment that item is done, before starting the next one**, and the same for a packet file, a leads file or a notes file. **Tell the user once, when you create the file, that work in progress is being saved in `ledger/` inside their copy of the repository, and that nothing is written anywhere else on their computer.** Never hold finished items in your head to write at the end: a session can stop without warning (a usage limit, a closed terminal), and whatever is not on disk is lost. Update the `meta` line's `items`, `minutes` and `fetches` at the end, or at wrap-up.

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
A landing page that says access is restricted, with no open record to read, is a `restricted` verdict, not a row. While exploring you may rule out things that were never in the queue; the check will note that, which is fine. Verdicts: `not_place_data`, `not_a_dataset` (paper, code, slides), `out_of_scope` (not health-relevant, or microdata of individuals), `restricted`, `blocked`, `duplicate_of:<inventory id>`. Every family you finish ends as a row (new, or an update to an existing one with the family's DOI in `notes`) or a verdict.

**Schema records** (packet c): set `schema_source` (the record URL), `schema_checked_on` (today), `place_key_system`, `place_key_vintage`, and where empty `columns_found` (semicolon list, first 40), `place_key_found`, `geometry_found`, `crs`, `years_found`. Also write `ledger/packets/<id>.json`:
`{"id", "schema_source", "route", "columns": [{"name", "type", "meaning"}], "place_key": {"column", "system", "level", "vintage", "basis"}, "geometry": {"kind": "embedded|reference|none", "type", "crs", "reference"}, "years_found", "not_read": ["sample_rows", "value_coding", "missing_coding"], "evidence": [urls], "notes"}`. A schema read is not a page verification: don't set `verification_level` or `file_verified`.

**Person-read** (packet d): the user tells you what the page says; you write the record with the user's URL as evidence and `"note": "person-read by <handle>"`. If the page opens for a person and that was the only blocker, set `url_health` to `ok-browser`.

**Never set:** `verify_tier`, `tier`, `health_score`, `checks_*`, `all_passing`, `verify_blockers`, `verified_on`, `partB_*`, `tier_cap`, or `round` on an existing row.

## 6. Finish

1. `git fetch origin`, then `python scripts/validate.py ledger/<your file>.jsonl --against origin/main`. Fix every error in your own file. If it says instead that the repository's own ledger does not replay, that is not the user's doing and you can't fix it: tell them to let a maintainer know, leave their file saved, and stop (it can be submitted once it's fixed). If it says a row was changed on main since you started, run `git pull --ff-only`, then `lookup.py --id` for that row, and reconsider your record.
2. Tell the user in 3-5 lines: items done against items claimed, checks settled, rows added, candidates ruled out, what was blocked, anything that looked wrong in an existing row, and what the session took against the estimate.
3. Ask one question: **"Submit this?"** On yes, do all of it yourself, in this order: `git switch -c work/<handle>-<YYYYMMDD-HHMM>` (the new file comes along), `git add ledger/`, `git commit -m "Inventory: <kind> (<n> items)"`, `git push -u origin HEAD`, `gh pr create --title "Inventory: <kind>, <n> items" --body "Closes #<claim issue>. <your summary>"`, and finally `git switch main` so the folder is left where it started. No AI attribution lines anywhere. Tell the user the PR link and that GitHub will check it and merge it by itself within a few minutes if it passes, and close their claim; nothing more is needed from them. (The check takes about half a minute to appear; if you look, wait before `gh pr checks`.)
4. If the user comes back saying the check failed: `gh pr checks`, read the failing log (`gh run view --log-failed`), `git switch` to that PR's branch, fix the ledger file, commit, push, and `git switch main` again.

## 7. Status, wrap up early, or recover an unfinished session

**Status** ("/inventory status", "where was I", "what's the state of my work"): run `python scripts/status.py`, show its output as it is, and stop. Change nothing: no pull, no branch switch, no claim, no submit. If it lists things to decide, say what each choice would do in one line each and wait for the user to pick. Don't recommend wrapping up or continuing unless asked.

**Wrap up** ("wrap up", "finish now", "stop here", or you are told a limit is near): stop after the item in hand; don't start another. If the item in hand is half-read, drop it (it stays in the queue) unless one more fetch finishes it. Then:

1. Make sure every finished item is in the ledger file. Update the `meta` line: `items` actually finished, `minutes`, `fetches`.
2. Run section 6 as usual: validate, a short summary that says how many of the claimed items were done, "Submit this?", then branch, commit, push, pull request with `Closes #<claim>`, back to `main`. The items you didn't reach return to the queue when the claim closes.
3. If nothing was finished: delete the empty ledger file and release the claim: `gh issue close <claim> --comment "Released: nothing done."`.

**Recover** (at the start of a session you find a ledger file that was never submitted):

1. Run `python scripts/status.py` and show the user what it found: which kind of work, how many items were saved, which claim, how many items are left in it.
2. Ask one question: submit what was saved, continue the claim from where it stopped, or discard it.
   - **Submit:** fix the `meta` counts from the records, then section 6.
   - **Continue:** `python scripts/queue.py --issue <claim>` lists the claim's items; the ones with a record in the file are done, carry on with the rest, appending to the same file.
   - **Discard:** move the file to `.inventory-discarded/` in the repo folder (git ignores it; create it if needed) and tell the user that is where it went; never delete their work, and release the claim: `gh issue close <claim> --comment "Released: session abandoned."`.
3. If there is no ledger file but `gh issue list --label claim --assignee @me --state open` shows a claim of theirs with nothing submitted, say so and ask whether to continue it or release it.
