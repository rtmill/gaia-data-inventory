---
name: inventory-maintainer
description: Maintainer tasks for the Gaia data inventory - reviewing contribution PRs, policy and method changes, running big discovery iterations, rebuilding, and releasing snapshots to OHDSI/GIS. Use when a maintainer asks for any of these.
---

# Inventory maintainer

Maintainers: Robert (rtmill) and whoever he adds. Contributors use the `inventory` skill; this one is for changes to the rules and for releases.

## Reviewing a contribution PR

CI (`validate.yml`) already checks shape, vocabulary, evidence, unit terms, that the file applies, and overlap with `main`. A human review is for judgement, and is optional for `ledger/`-only PRs (CODEOWNERS doesn't require it). When reviewing, spot-check 2-3 records: open the evidence URL, confirm the value. Watch for values that look like memory rather than reading (round years, generic licence names, units not on the page), new rows that duplicate an existing family, and `public_domain_us_federal` on non-federal hosts.

## Policy and method changes (need a maintainer)

- **Tier rules** live in `scripts/inv.py` (`tier_of`). Changing them re-tiers every row on the next build: run `python scripts/build.py` locally first and read the tier counts before and after. Record the decision in `method/decisions.md` with the date.
- **New columns** come in through a maintainer ledger file (`packet: "m"`, validated with `--maintainer`): the first record that sets a new column adds it.
- **Hand caps:** set `tier_cap` ("Silver: geometry dependency TBD") in a maintainer record; `tier_of` respects it.
- **Unit vocabulary, anchors:** `method/unit-vocabulary.csv`, `method/anchors.csv`; dated note per change.
- **Open WG questions** (don't decide them in a PR): `method/TODO.md` tier 4 (Silver rule 4.10, site-wide terms 4.8, non-commercial sources 4.5, person-level records 4.3).

## Big iterations (sweeps, spikes, new methods)

Run them as before, one job at a time on Sonnet with caps and a checkpoint, from a branch of this repo. Output: one ledger file (`<date>-<handle>-p<N>-<slug>.jsonl`, `packet: "m"` where it adds columns) plus `method/iterations/<NN>-<slug>/` with `approach.md` (the prompt) and `results.md` (the report), and a row in `method/iterations/README.md`. Expect the build to show the tier moves; zero moves for label-only work.

## Releasing to OHDSI/GIS

Nothing goes to GIS without a maintainer's explicit go.

1. Make sure `main` is built (CI does it on every push).
2. **Actions → "Release snapshot to OHDSI/GIS" → Run workflow.** It runs `scripts/export_gis.py`, pushes a branch to the maintainer's GIS fork and opens a PR on OHDSI/GIS with the snapshot (`exploration/place-data-inventory/` data and README, `rmd/data/inventory*.json`, `rmd/inventory.Rmd`, `rmd/assets/inventory.js`). It needs the `GIS_FORK_TOKEN` secret (a fine-grained token with contents and pull-request write on the fork only).
3. Without the workflow: `python scripts/export_gis.py /tmp/gis-export`, copy it into a GIS clone on a new branch from `origin/main`, review `git diff --stat`, commit as `rtmill <rtmiller645@gmail.com>`, push, `gh pr create -R OHDSI/GIS`. Use `Refs OHDSI/gaiaCatalog#N` one per line (a bare `#N` links GIS issues).
4. Merge in GIS: the site rebuilds on merge.

## Contracts with OHDSI/GIS (don't break these)

- **`rmd/data/inventory.json` is read by GIS's own `scripts/link_use_cases.py`** (Jared, 2026-11-07), which matches use-case data needs to inventory rows by `id`, `th` (themes), `u` (unit) and `rg` (region) during the GIS site build. Keep those keys and their meaning stable in `build.py`; a change there needs a heads-up to Jared and a matching GIS change.
- **`site/inventory.Rmd` and `site/inventory.js` are copies of the GIS page.** People edit the page in GIS too (Jared did on 2026-11-17). Before each release, diff `site/` against GIS `main` and take their edits into `site/` first, or the release reverts them.

## Rebuild and checks

- `python scripts/build.py` rebuilds `build/` and the README state block; `--check` fails if `build/` is stale.
- `python scripts/validate.py --changed --against origin/main` checks the branch's ledger files.
- `python scripts/sync_issues.py --dry-run` shows which claim issues would be closed or nudged.
- **Estimates:** `method/estimates.csv` holds the per-item figures measured on earlier runs; `queue.py` switches a kind to the median of real sessions once `build/effort.csv` has three. Update the file when a big run gives a better figure, with its basis.
