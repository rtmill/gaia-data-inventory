# Breadth test of the contributor flow (2026-11-18)

Claude Code prompt. Run in a **fresh clone** of `rtmill/gaia-data-inventory` (not the authoring copy), on Sonnet, with `gh` signed in as `rtmill`. Unattended. **Time box: about 90 minutes.** One step at a time, no sub-agents.

> **This assumes:** (1) the contributions made here are real reads and stay in the inventory; (2) you follow `.claude/skills/inventory/SKILL.md` exactly as a contributor would, and where it is unclear you do the most literal thing and log it, instead of filling the gap from this brief; (3) nobody is there to answer questions, so every choice the skill would ask the user for is given below.

## What this is for

The contributor flow has only been tested on the menu. Nothing has gone from a claim to a merged contribution. This run takes a small amount of every kind of work through the whole loop, then tries the failure paths, and writes down everything that broke, was unclear, or cost more or less than estimated.

## Rules

- Handle: `rtmill`. Amount per test: as stated below (small on purpose). Answer "yes" to "Submit this?".
- Follow the skill's own caps and rules (evidence for every value, no sign-ins, no data files, no bot-check workarounds).
- After each submitted pull request, wait for it: `gh pr checks <n> --watch`, then confirm it merged (`gh pr view <n> --json state,mergedAt`). Then `git switch main && git pull --ff-only` and wait until a "Build: replay ledger" commit has arrived if the build changed anything (poll `git pull` up to 3 minutes).
- After each merge, check and record: the claim issue is closed; `python scripts/queue.py` shows fewer items of that kind (or the same, if the items still have open checks: say which); `build/effort.csv` has the session's line; the datasets' rows show the change (`python scripts/lookup.py --id <id>`).
- **Log as you go** in a scratch file outside git (`../breadth-test-log.md`): for each test, what you did, what happened, pass or fail per check, items done, minutes, fetches, and every place the skill or the docs were unclear, wrong or missing. Tokens: if you can read this session's transcript under `~/.claude/projects/` and sum the usage between the test's start and end, record it and say how you got it; otherwise write "not measured".
- If a step fails in a way that blocks the rest (cannot claim, cannot push, checks never start), log it, skip the tests that depend on it, and go to "Findings".
- If a **failure-path** pull request (F1, F2, F4) merges, stop everything and say so at the top of the findings: that is a serious defect.

## Tests, in order

| # | Work | What to take | Extra things to confirm |
|---|---|---|---|
| T1 | Add or rule out a lead (`candidate`) | 3 items, default order | At least one ends as a row or as a ruled-out lead; the ruled-out one appears in `build/candidates-rejected.csv`; a new dataset gets a tier |
| T2 | Check an unverified dataset (`read`) | 2 items | A tier changes, or you can say why not; `verified_on` is set |
| T3 | Fill in thin evidence (`settle`) | 2 items | Checks already settled on the row are untouched |
| T4 | Record columns and place key (`schema`) | 2 items | `ledger/packets/<id>.json` exists; `verified_on` is **not** changed; the item leaves the schema queue |
| T5 | Find where a dead link went (`successor`) | 1 item | The note says a web search was used |
| T6 | A dataset you name (no claim) | "Social Vulnerability Index" (expect: already in, so an update or nothing), then "Eviction Lab eviction data" (expect: check, then a new row if it is not in) | The duplicate check works; no claim issue is opened |
| T7 | Find new datasets: continue an approach (`explore`) | "Place-key search": read 3 of the unread keyed datasets; if the list of them is not in this repo, say so and instead run 2 searches for one untried key system | A `ledger/leads/*.csv` and a `ledger/notes/*.md` are written; after merge the leads appear as `candidate` items |
| T8 | Find new datasets: something new (`explore`) | Idea: "datasets published in Zenodo communities of exposome research projects (for example EXPANSE, ATHLETE, EHEN)". Cap: list at most 20 records, read at most 3 | The skill's check against earlier approaches happens; a brief is written into the note before the run |
| T9 | You open a blocked page (`person-read`) | Do not do the reads (no person is present). Only: slice the queue for this kind, show what 2 items would be, and log whether the skill's instructions for this path are complete | Marked "not run: needs a person" |

Also during T1: before claiming, run `python scripts/queue.py --by region --kind candidate` and `--by category --kind candidate`, and take the 3 items with a filter (`--category care_sites` if any exist, otherwise no filter). Log whether slicing behaved as the docs say.

## Failure paths

| # | Test | Expected |
|---|---|---|
| F1 | On a branch `test/bad-file`, add `ledger/<today>-rtmill-test-bad.jsonl` with one record that sets `chk_unit` to `"good"` and `verify_tier` to `"Gold"` on a real id. Push, open a pull request titled "TEST: must fail" | The check goes red and names both errors; nothing merges. Then close the pull request and delete the branch |
| F2 | Overlap. Find the main commit just before T2's merge (`git log`). Create `test/overlap` from it, add a ledger file that sets one check on a dataset T2 changed, push, open "TEST: overlap must fail" | The check goes red with "was changed on origin/main since you branched". Close and delete |
| F3 | Abandoned claim. Claim 2 `read` items, confirm `python scripts/queue.py --kind read --n 5` no longer offers them, then close the claim issue without doing them and confirm they are offered again | As described |
| F4 | A change outside `ledger/`: this is the findings pull request below | The check passes but the pull request is **not** merged, and the log says it is waiting for a maintainer |

## Findings (always do this, even if stopped early)

1. `git switch -c test/findings-<today>` and write `method/tests/findings-<today>.md`: the log, tidied. Start with a table: test, ran or not, passed or failed, items, minutes, fetches, tokens. Then, most important first: defects (what broke), unclear or wrong instructions (quote the sentence and say what you did), estimates against actuals per kind, and suggestions. Keep it factual; no praise.
2. Commit, push, and open a pull request titled "Breadth test findings <today>". Do not merge it. Confirm F4's expectation and add the result as a comment on the pull request.
3. `git switch main`. End with a five-line summary in the terminal.
