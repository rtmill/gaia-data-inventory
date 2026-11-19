# Zenodo communities of exposome projects (2026-11-18, rtmill)

## Brief (written before the run)

- **Question:** do the Zenodo communities of exposome research projects (EXPANSE, ATHLETE, EHEN) hold place-keyed datasets (exposure surfaces, area indicators) that the inventory does not have?
- **Where it looks:** Zenodo `/api/communities?q=<project>` to find each community's slug, then `/api/records?communities=<slug>` for up to 20 records in all. Metadata only; the record JSON is the read.
- **What counts as a hit:** a record that is a reusable dataset (not a paper, code or slides) with place-keyed values or geometry, open access, and not already in the inventory (`lookup.py`).
- **Caps:** at most 20 records listed, at most 3 read in full, no data files, no sign-ins, 1 request per second, no sub-agents.
- **Worth scaling if:** at least 3 of the 20 listed are new place-keyed datasets, or at least one community lists more than 20 data records.
- **Checked against earlier approaches** (`queue.py --approaches`; `--approaches --all` does not exist in this version, so `method/approaches.csv` was searched for exposome, Zenodo, communities): closest are "Sources named in review papers" (exposome reviews, not run, needs a maintainer brief) and "Candidate pool through repository records" (Zenodo records reached from DataCite candidates). Neither lists a project's Zenodo community, and neither is closed, so this is a new variant, not a repeat.

## Run

**Communities.** `api/communities?q=` for EXPANSE (949 hits, none the project), ATHLETE (629, none) and EHEN (28; `ehen` is the project's community). A fourth query, `exposome`, listed related communities; four were used: `drinkingwaterexposomeatlas` (19 records), `geospace` (2), `cropland_soil_exposure` (0), `heap-exposome` (40; most are project deliverables, publications). Searches/requests: 3 community searches + 1 exposome community search + 5 record listings = 9; plus 5 record reads (3 distinct records; two were fetched twice) = 14 requests.

**Counts.** Listed 13 records (cap 20) from the `ehen` community (1) and the other four (12 shown, size 5 each). Types: 4 datasets, 9 publications. Found 4 datasets, already known 0, new 4, read 3, added 0 rows, ruled out 3, left as a lead 1 (EHEN on-line toolbox, record not read). Records listed beyond the first 5 of each community were not seen (drinking-water atlas 19, heap-exposome 40).

**Hit rate against the brief:** 0 new place-keyed datasets of the 13 listed (needed 3 to scale). Precision 0 of 3 read. What the three are: a catalogue of other datasets' variables, a literature-association table, and an undescribed survey spreadsheet.

**What blocked.** Nothing was blocked. EXPANSE and ATHLETE have no Zenodo community of their own; their outputs are not reachable through this route.

## Verdict
**Drop** as a route to place-keyed data: these communities hold project deliverables, tools and papers. One narrow point: the Drinking Water Exposome Atlas community (19 records) might deserve one listing of its remaining 14 records, since the one dataset shown there was an unknown spreadsheet; not worth a separate approach.
