# Gaia data inventory

**What this is.** Health researchers who want to link where patients live to their surroundings (air quality, heat, deprivation, distance to care) need public datasets that are keyed to places. [Gaia](https://github.com/OHDSI/GIS), the OHDSI GIS working group's toolkit, loads such datasets and joins them to patient locations. But before a dataset can be loaded, someone has to find it and establish the basics: is it still published, what is its licence, which years and which geography does it cover, how do you get it, and what column ties it to a map. This repository is the working group's shared record of that: every public place-based dataset we have looked at, what has been confirmed about it, and the link where each fact was read.

It is a list of **prospects**, not the Gaia catalog. Only a few of these datasets can be loaded into Gaia today.

**This is a crowdsourcing effort: divide and conquer.** Finding and checking datasets is slow, and most of the reading is done by Claude, which costs tokens. No one person has enough of either. So the working group shares it out: anyone can take as much or as little of the open work as they choose, for ten minutes or an afternoon. That is why this is its own repository, and it is built around making shared work safe:

- **Every fact carries its link.** Nothing is entered from memory, a person's or an AI's, so anyone can check anyone else's work.
- **Nobody edits the list by hand.** A contribution is a small file of changes. The list is rebuilt from the starting point plus every contribution, automatically. Two people can't overwrite each other, and the record of who confirmed what, from where, is kept.
- **Open work is laid out with what it costs and what it produces,** so you can see where your time or tokens do the most and take exactly as much as you want.
- **What was tried is written down:** each way of finding data, how well it worked, and what's left of it, so the next person continues instead of starting over.

## The path a dataset takes

The end point is a dataset that Gaia can load and join to patient locations. Getting there takes six steps, and the work in this repository is organised around them:

| Stage | What it means | How a dataset gets there |
|---|---|---|
| 1. **Lead** | Something that might be a usable dataset: a reference turned up by a search | Someone explores: continues a way of searching, or tries a new one |
| 2. **Listed** | In the inventory, with a name, publisher and address, but nothing confirmed | A lead is looked at and kept (or ruled out), or someone adds a dataset they know |
| 3. **Verified** | Still published, with its licence, years, geography and way of access confirmed, each with the link it was read from | Someone reads the publisher's pages |
| 4. **Fully specified** | Its columns, the column that ties it to a map, which geography and vintage that is, and its geometry are recorded | Someone reads its metadata, or opens a file |
| 5. **Recipe drafted** | A loading recipe is written in Gaia's recipe format: where to fetch it, how to map it, what each variable is | Someone writes it from the specification. *Not open yet: the working group is settling the recipe format ([gaiaCatalog #44](https://github.com/OHDSI/gaiaCatalog/pull/44))* |
| 6. **In the Gaia catalog** | The recipe has been tested and merged into [gaiaCatalog](https://github.com/OHDSI/gaiaCatalog); the dataset can be loaded | Gaia's maintainers, outside this repository |

Each kind of work you can take on moves datasets one step along this path. Most datasets are still in the early stages:

<!-- state:start -->
**As of 2026-11-19:** 823 datasets assessed, **645 verified** (Gold 157, Silver 488), Bronze 107, Browser needed 20, Failed 28. 15 file-verified; 36 with a schema record; 10 state their place-key vintage.

**Where things stand:** 270 leads not yet looked at → 155 listed but unverified → 645 verified (94 of them on thin evidence) → 16 fully specified → 0 with a draft recipe → 35 in the Gaia catalog. Open work: 548 items; see it with `python scripts/queue.py`. **Ledger:** 11 contribution files from 1 contributor.
<!-- state:end -->

Browse it on the GIS site: **[Data Inventory](https://ohdsi.github.io/GIS/inventory.html)**.

## Contribute

Choose what to work on and how much, let Claude do the reading on your own Claude usage (the tokens are your contribution), approve the result.

**Before you start (once per computer).** You need four things:

| You need | How to get it |
|---|---|
| Claude Code | https://claude.com/claude-code |
| Python 3.9 or later | https://www.python.org/downloads (on Windows, tick "Add python.exe to PATH") |
| The GitHub CLI, signed in | Windows: `winget install --id GitHub.cli` · macOS: `brew install gh` · Linux: https://cli.github.com. Then `gh auth login` (GitHub.com, HTTPS, yes to authenticating Git, sign in through the browser) |
| Write access to this repository | Ask Robert (rtmill) to add your GitHub account, then accept the emailed invitation |

To check all of it at once, after cloning: `python scripts/preflight.py`. It says what's missing and the exact command to fix it. `/inventory` runs the same check and stops with those steps if anything is missing.

1. Clone the repo and start Claude Code in it:
   ```bash
   git clone https://github.com/rtmill/gaia-data-inventory
   cd gaia-data-inventory
   claude
   ```
2. Type `/inventory` and answer its questions: which kind of work, how much of it, and at the end whether to submit.

That's all you do. Claude shows you the open work and what it costs, reserves the items you pick, does the work, and submits it; the checks, the merge and the rebuild are automatic. Work in progress is saved as you go in the `ledger/` folder of your copy, and nowhere else on your computer, so a session that stops early loses nothing. Details: [CONTRIBUTING.md](CONTRIBUTING.md). To suggest a dataset without any of this, [open an issue](../../issues/new?template=suggest-dataset.yml).

## How it works

```
base/inventory-base.csv   the inventory as of 2026-11-18 (frozen)
        + ledger/*.jsonl   every change since, one file per contribution, applied in file-name order
        = build/           the current inventory, queues and site data (generated by CI; never edited by hand)
```

- **Nobody edits the CSVs.** A contribution is a ledger file of small change records, each with the URL it was read from. `scripts/build.py` replays base + ledger, recomputes tiers and the work queue, and CI commits the result.
- **Tiers.** Gold: link, page, licence, unit, years and access all pass. Silver: live, read, and no fail among licence, unit, years, recency. Bronze: live, not fully read. Browser needed: the site blocks scripts. Failed: dead, withdrawn, or data before 2000. Rules in `scripts/inv.py` (`tier_of`).
- **Method and history** are in `method/`: the page-read brief, unit vocabulary, anchors (what we measure coverage against), the TODO, and every iteration that built the inventory (`method/iterations/`).

| Folder | What it is |
|---|---|
| `build/inventory-verified.csv` | Gold and Silver, readable columns |
| `build/inventory-all.csv` | Every dataset, every check, detail and evidence |
| `build/queue.csv` | Every open item of work (`python scripts/queue.py` slices it, estimates it and claims from it) |
| `ledger/` | Contributions (append-only) |
| `base/` | The frozen starting point and the candidate families still to check |
| `method/` | How it was built and how to work on it |
| `site/` | Source of the GIS site's Data Inventory page |

## Licence

Data (`base/`, `ledger/`, `build/`): [CC BY 4.0](LICENSE-DATA.md). Code (`scripts/`, `site/`, `.claude/`, `.github/`): [Apache-2.0](LICENSE). The datasets listed keep their own licences, recorded per row.
