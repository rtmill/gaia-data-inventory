# Contributing

> **This assumes:** (1) you have Claude Code and push access to this repo (ask Robert); (2) you add **ledger files**, never edits to the CSVs in `base/` or `build/`; (3) every value you add was read on the publisher's page, its repository record or its metadata record, and that URL is kept as evidence.

## Start (5 minutes)

1. Open the **[batch issues](../../issues?q=is%3Aissue+is%3Aopen+label%3Abatch)**, pick one nobody is assigned to, and **assign yourself**. That's the claim.
2. Clone, branch, start Claude Code (Sonnet is enough: `/model sonnet`):
   ```bash
   git clone https://github.com/rtmill/gaia-data-inventory && cd gaia-data-inventory
   git switch -c batch/<BATCH>-<your-handle>
   claude
   ```
3. Type **`/inventory <BATCH>`** (for example `/inventory BR-03`). Claude reads the batch, tells you the caps, works through it, writes `ledger/<date>-<handle>-<batch>.jsonl`, and checks it.
4. Commit that file (and `ledger/packets/*.json` for packet c), push, and open a PR with `Closes #<issue>` in the text. CI checks it. If it's green, you can merge it yourself.

No batch in mind? `/inventory` alone shows the menu, including "a dataset I know".

## The packets

| Packet | Queue | You do | Size |
|---|---|---|---|
| **a** | none | Name a dataset; Claude checks whether it's in, and if not, reads its page and drafts a row | 1 row, ~15 min |
| **b** | `BR` Bronze reads, `SO` Silver with open checks, `FS` failed rows | Settle open checks from publisher pages, or find a successor | 10 rows, 30-60 min |
| **c** | `RR` recipe-ready | Columns, place key (system, level, vintage), geometry and years from metadata records | 5 rows, 30-60 min |
| **d** | `BN` browser-needed | Open pages that block scripts in your own browser; Claude only formats what you report | 10 rows, ~5 min each, almost no tokens |
| **e** | `CA` candidates | Check 10 candidate families from DataCite: add the real datasets as rows, rule out the rest | 10 families, ~45 min |

## Rules (Claude follows these; so should you)

- **Evidence URL for every value.** Not from memory, a search snippet or another AI. Unread means `not_checked`.
- **No sign-ins, registrations, form submissions, bot-check workarounds, or data-file downloads.** Blocked pages are recorded as blocked (and become packet d).
- **Units from `method/unit-vocabulary.csv`.** If none fits, say so in the PR; don't invent one.
- **Person-level records stay out** (registries of named individuals and the like).
- **Ledger only.** Don't edit `base/`, `build/`, `method/`, `scripts/` or `.claude/` in a contribution PR; those need a maintainer's review (CODEOWNERS).

## If CI fails

- **"was changed on origin/main since you branched"**: someone settled the same row first. Re-check that row against what's on `main` now (`python scripts/lookup.py --id <id>`), drop or update your record, `git rebase origin/main`, push again.
- **Anything else**: run `python scripts/validate.py --changed` locally; the message says which line and why.

## What happens after merge

CI replays the ledger, rebuilds `build/`, recomputes tiers, closes your batch issue and opens new ones. Your handle goes into each row's change note. A maintainer releases snapshots to the OHDSI GIS site.
