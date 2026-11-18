# Contributing

> **This assumes:** (1) you have Claude Code, the `gh` CLI signed in, and push access to this repo (ask Robert); (2) you add **ledger files**, never edits to the CSVs in `base/` or `build/`; (3) every value you add was read on the publisher's page, its repository record or its metadata record, and that URL is kept as evidence.

## Start (5 minutes)

```bash
git clone https://github.com/rtmill/gaia-data-inventory && cd gaia-data-inventory
git switch -c work/<your-handle>-<date>
claude            # Sonnet is enough: /model sonnet
```

Then type **`/inventory`**. Claude shows the queue, with what each kind of work costs, and asks how much you want to take. You decide; nothing is pre-assigned.

You can look first without Claude:

```bash
python scripts/queue.py                                    # what's open, and the cost per item
python scripts/queue.py --by region --kind candidate       # slice it: region, category, host, publisher, tier
python scripts/queue.py --kind candidate --region Africa --n 15            # what 15 of those would be, and the estimate
python scripts/queue.py --kind candidate --region Africa --n 15 --claim    # take them (opens an issue assigned to you)
```

Claiming opens a `[claim]` issue listing your items; they disappear from everyone else's queue until the issue closes. Work it with `/inventory <issue number>`. When done, commit the one file in `ledger/`, push, and open a PR with `Closes #<issue>`. CI checks it; if it's green, merge it yourself. Whatever you didn't finish goes back to the queue.

## Kinds of work

| Kind | What you do | Estimate per item (from earlier runs; `queue.py` shows the current figures) |
|---|---|---|
| `candidate` | Check a DataCite candidate family: add the real dataset as a row, or rule it out | ~2 min; about 1 in 6 becomes a row |
| `read` | Read a Bronze row's publisher page and settle its checks | ~2.5 min, ~16k tokens |
| `settle` | Silver rows with most checks still open: settle them | ~2.5 min, ~16k tokens |
| `schema` | Columns, place key (system, level, vintage), geometry and years from metadata records | ~1 min |
| `successor` | A failed row: find where it moved, or confirm it's retired | ~3 min; about half resolve |
| `person-read` | Open a page that blocks scripts in your own browser; Claude only formats what you report | ~5 min of yours, almost no tokens |
| a dataset you know | Name it; Claude checks whether it's in, and if not drafts a row (no claim needed) | ~15 min |

Estimates start from measured runs (`method/estimates.csv`) and update from what sessions here actually take: each ledger file's first line records items, minutes and fetches, and tokens if you give Claude your `/cost` total.

## Rules (Claude follows these; so should you)

- **Evidence URL for every value.** Not from memory, a search snippet or another AI. Unread means `not_checked`.
- **No sign-ins, registrations, form submissions, bot-check workarounds, or data-file downloads.** Blocked pages are recorded as blocked (and become `person-read` items).
- **Units from `method/unit-vocabulary.csv`.** If none fits, say so in the PR; don't invent one.
- **Person-level records stay out** (registries of named individuals and the like).
- **Ledger only.** Don't edit `base/`, `build/`, `method/`, `scripts/` or `.claude/` in a contribution PR; those need a maintainer's review (CODEOWNERS).

## If CI fails

- **"was changed on origin/main since you branched"**: someone settled the same row first. Re-check that row against what's on `main` now (`python scripts/lookup.py --id <id>`), drop or update your record, `git rebase origin/main`, push again.
- **Anything else**: run `python scripts/validate.py --changed` locally; the message says which line and why.

## What happens after merge

CI replays the ledger, rebuilds `build/` (inventory, queue, site data), recomputes tiers and closes your claim. Your handle goes into each row's change note. A maintainer releases snapshots to the OHDSI GIS site.
