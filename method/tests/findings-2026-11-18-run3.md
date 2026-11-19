# Breadth test findings, run 3 (2026-11-18)

Third run of `breadth-test-2026-11-18.md`. Skipped as asked: T1, T2, F3 (passed earlier). T9 was not in the list for this run and was not run (it needs a person). Run in the authoring copy, not a fresh clone, on `main`.

> **No failure-path pull request merged.** F1 (#35) and F2 (#33, #34) went red and were closed; F4 is this pull request. The contribution path works end to end again after the `tier_cap` fix: T3, T4, T5, T7 and T8 each went from a pull request to a merged contribution, a closed claim and a rebuilt inventory. The defects below are smaller.

## Results

| Test | Ran | Result | Items | Minutes | Fetches | Tokens |
|---|---|---|---|---|---|---|
| `/inventory status` | yes | found the unsubmitted settle file and claim #29 | - | 1 | 0 | not measured |
| T3 settle (submit) | yes | **passed**: PR #32 merged about 1 min after opening; claim #29 closed; effort line present; rows changed | 2 | 9 (read, run 2) + about 3 to submit | 7 (run 2) | not measured |
| F2 overlap | yes | **#33 red for the wrong reason** (old base has no `scripts/selftest.py`); **#34, from a newer base, red with the right message**. Neither merged | 1 + 1 | about 8 | 0 | not measured |
| F1 bad file | yes | **red, names both errors** (#35). Not merged | 1 | about 3 | 0 | not measured |
| T4 schema | yes | **passed** for 1 of 2 items (PR #37); the other (AHRQ CLH) is blocked by a 403 and could not be recorded | 1 of 2 | about 12 | 7 | not measured |
| T5 successor | yes | **passed** (PR #39); the note says a web search was used; tier Failed to Bronze | 1 | about 6 | 4 (+1 search) | not measured |
| T6 named dataset | lookups; reads blocked | duplicate check works; no claim opened; Eviction Lab page is blocked (403), so nothing to submit | 0 | about 3 | 3 | not measured |
| T7 explore: continue | yes, fallback path | **passed with 0 leads** (PR #41); the unread list is not in the repo, so 2 DGUID searches ran | 0 | about 10 | 6 | not measured |
| T8 explore: new | yes | **passed** (PR #43); brief written first; check against earlier approaches done by hand; 3 ruled out, 1 lead (now a `candidate` item) | 3 | about 14 | 14 | not measured |
| T9 person-read | no | not run: needs a person | - | - | - | - |
| F4 change outside `ledger/` | yes (this PR) | see the comment on the PR | - | - | - | - |

Tokens: not measured (the session transcript was not summed). Minutes are wall clock, approximate. "Fetches" counts requests including re-fetches.

## Defects

1. **F2's first pull request (#33) went red for an unrelated reason, so the brief's own F2 recipe no longer works.** The brief says to branch from "the main commit just before T2's merge" (`f69bc3a`). That commit predates `scripts/selftest.py` (added in `f0c71d9`), and CI checks out the branch tip, so the first step, `python scripts/selftest.py`, fails with "can't open file" and the overlap step is skipped. Any branch started before the self-test existed hits this. I re-ran from `ccfa58d` (after the self-test, before #32) with a check on `global_gdl_shdi`, which #32 changed. #34 went red with "global_gdl_shdi was changed on origin/main since you branched (2026-11-18-rtmill-settle-two.jsonl): re-check it, then rebase". The brief needs a base commit chosen from current history.
2. **A blocked `schema` item cannot be recorded.** `validate.py` says "packet c needs ledger/packets/<id>.json" for a `schema` record with no packet, and the skill's blocked rule ("set no checks, note `blocked`") gives no record shape for it. I left `us_ahrq_sdoh_database` out of the file (AHRQ returned 403; openICPSR is blocked by policy), so `queue.py --kind schema` still offers it first: the next contributor will spend a read on it. It was also offered in run 2.
3. **`queue.py --approaches --all` does not exist.** The skill (1b step 3) and the last line of `--approaches` both tell the user to run it. It exits with "unrecognized arguments: --all". I read `method/approaches.csv` instead.
4. **The place-key approach's next step cannot be followed from the repo.** Its brief says to read the 33 unread keyed datasets. `k2-hits-classified.csv` is named in `results.md` but is not in `method/iterations/23-place-key-spike/` (only `approach.md`, `k0-summary.csv`, `k2-measures.csv`, `results.md`).
5. **Fetch cap exceeded once, by my slip.** In T5 I saved a fetched page to a temporary file outside the repository, could not read it back, and fetched the page again: 3 page fetches against a cap of 3, plus the dead original URL and the search. I deleted the temporary file at once; the project instruction says not to save fetched pages and I should not have. Nothing entered the repository and no evidence was affected.
6. **Slug rule and file names disagree.** The skill says the file is `<date>-<handle>-<slug>-<HHMM>.jsonl`. No file in `ledger/` has the `-<HHMM>` part and `validate.py` does not object, so I followed the existing names. Enforce it or drop it from the skill (run 2 found a name collision from the same cause).

## Unclear or wrong instructions

- Skill 3, "Records before pages": the FNAI metadata file (`flma_meta.htm`) is UTF-16 with a byte-order mark. Decoding it as UTF-8 or Latin-1 gave unreadable text and cost two extra fetches (6 requests, the cap for `schema`). Nothing in the skill covers metadata that is not UTF-8.
- Skill 1c step 2 ("Confirm before doing the work ... Ask: 'Is this the one you mean?'") cannot be followed unattended. The brief gave the answer, so I took the lookup matches as confirmed. Both named datasets were already in; the only open work was Eviction Lab's `join_key`, and its page is blocked, so 1c has no step for "already in, update wanted, page blocked". I stopped without writing.
- Skill 5, "Rule out a candidate (packet e only)": in T8 the three records I read came from a community listing, not the queue, and `validate.py` warns "candidate ... is not a lead in the queue" for each. They are accepted and appear in `build/candidates-rejected.csv`, but the warning reads like a problem. Say in the skill that explore reads may rule out DOIs that were never queued.
- Skill 1b step 6 says what to write for leads but not whether an empty run (T7) still writes a leads file. I wrote the run note and a session file with `items: 0`; it merged and the effort line shows 0 items. Fine, but unstated.
- Skill 3, 3-fetch cap for `successor`: a time-out on the old URL, the page that holds the successor and one more leave no room for the metadata XML that the successor page links to. I set only `chk_link_live` and left licence, unit and access open. That one check moved the tier from Failed to Bronze.
- `lookup.py "<DOI>"` with no match prints only the footer line ("A match >= 0.75 ... is already in"), with no "no match" line. The footer reads as if matches were hidden.

## What worked (facts to keep)

- `status.py` found the unsubmitted file and its claim. Submitting took under a minute of work; the check about 15 s; merge about a minute after opening; the build commit followed 1 to 3 minutes later.
- Checks already on `global_gdl_shdi` (licence, access: `warn`) were untouched by T3. `us_fnai_florida_managed_areas` changed only in the schema fields and the run note, with `verified_on` and tier untouched, and `ledger/packets/us_fnai_florida_managed_areas.json` exists. `pt_ine_bgri`, `global_gdl_shdi`, `eu_eea_aq_stations_rest` and the FNAI row left their queues after merge, even with checks still open.
- Claims #29, #36, #38, #40 and #42 closed on merge; effort lines are present for all five sessions.
- F1's red names both bad values (`chk_unit = 'good'` and `verify_tier is computed or fixed`). The run 2 crash on `tier_cap` is gone.
- Duplicate check: "Social Vulnerability Index" matched `us_cdc_svi` (0.80); "Eviction Lab eviction data" matched `us_eviction_lab` (0.82). No claim issue was opened for either.
- T8: the three DOIs ruled out are in `build/candidates-rejected.csv`; the EHEN toolbox lead (10.5281/zenodo.17639414) appears as a `candidate` item.

## Estimates against actuals

| Kind | Estimate per item | Actual |
|---|---|---|
| settle | about 2.5 min, 16k tokens | 4.5 min and 3.5 fetches per item (run 2); tokens not measured |
| schema | about 2 min, 16k tokens (a guess) | 12 min and 7 fetches for 1 item done (the blocked one cost 1 fetch; FNAI cost 6, two of them re-fetches for the encoding) |
| successor | about 3 min, 20k tokens (a guess) | 6 min, 4 requests and one search |
| explore | depends on the approach | DGUID: 10 min, 6 requests, 0 leads. Exposome: 14 min, 14 requests, 3 ruled out, 1 lead |

Every kind ran about twice the estimate in minutes. Fetches per item went above the caps' assumptions when something went wrong once (blocked page, encoding, dead URL).

## Suggestions

1. Give blocked `schema` items a record shape (a packet with `route: blocked`, or a verdict on the row) so they leave the queue or move to `person-read`.
2. Implement `--approaches --all`, or remove it from the skill and from the script's last line.
3. Commit the unread keyed list (`k2-hits-classified.csv`, or the 33 ids) so the place-key approach can be continued.
4. Rewrite F2 in the brief: "branch from the newest main commit before the last merge that changed the dataset", and run the self-test locally first.
5. Mention non-UTF-8 metadata in the skill's records list, or add a helper that decodes a fetched page.
6. Reword the "not a lead in the queue" warning for explore reads, and have `lookup.py` say when nothing matched.
