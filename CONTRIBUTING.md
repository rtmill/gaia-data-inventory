# Contributing

The inventory is crowdsourced: divide and conquer. You take whatever share of the open work you choose; Claude does the reading on your Claude usage, so the tokens it takes are what you are contributing; and what you submit is merged into the shared list automatically.

> **This assumes:** (1) you have Claude Code, the `gh` CLI signed in, and push access to this repo (ask Robert); (2) you add **ledger files**, never edits to the CSVs in `base/` or `build/`; (3) every value you add was read on the publisher's page, its repository record or its metadata record, and that URL is kept as evidence.

## Before you start (once per computer)

| You need | How to get it |
|---|---|
| Claude Code | https://claude.com/claude-code |
| Python 3.9 or later | https://www.python.org/downloads (on Windows, tick "Add python.exe to PATH") |
| The GitHub CLI, signed in | Windows: `winget install --id GitHub.cli` · macOS: `brew install gh` · Linux: https://cli.github.com. Then `gh auth login` (GitHub.com, HTTPS, yes to authenticating Git, sign in through the browser) |
| Write access to this repository | Ask Robert (rtmill) to add your GitHub account, then accept the emailed invitation |

To check all of it at once, after cloning: `python scripts/preflight.py`. It says what's missing and the exact command to fix it. `/inventory` runs the same check and stops with those steps if anything is missing.

## What you do

1. Clone the repo and start Claude Code in it (Sonnet is enough: `/model sonnet`):
   ```bash
   git clone https://github.com/rtmill/gaia-data-inventory
   cd gaia-data-inventory
   claude
   ```
2. Type `/inventory` and answer its questions: which kind of work, how much of it, and at the end whether to submit.

## What happens, in order

| Step | Who does it |
|---|---|
| Shows the open work by kind, with the cost per item in minutes and tokens | Claude |
| You say which kind and how much (a number of items, or a time or token budget); you can narrow by region, topic, publisher or site | **You** |
| Reserves those items: opens a GitHub issue titled `[claim] …`, assigned to you, so nobody else takes them | Claude |
| Reads the pages and writes one file under `ledger/` | Claude |
| Checks the file, shows you a summary, asks whether to submit | Claude |
| You say yes | **You** |
| Makes a branch, commits, pushes, opens a pull request that closes your claim | Claude |
| Checks the pull request, merges it if it only adds ledger files and passes, rebuilds the inventory and the queue | GitHub Actions |

Anything you reserved but didn't finish goes back to the queue when the claim closes. To look at the queue without Claude: `python scripts/queue.py` (`--help` for slicing and claiming by hand).

## What you can take on

A dataset moves through six stages (the README has the full table): **lead** → **listed** → **verified** → **fully specified** → **recipe drafted** → **in the Gaia catalog**, where it can finally be loaded. Each kind of work moves datasets one stage. Drafting recipes is not open yet: it waits for the working group to settle the recipe format. `/inventory` shows live counts, costs and what 30 minutes buys.

| Work | Takes a dataset from → to | What you end up with |
|---|---|---|
| `explore` | nothing → lead | New leads for the queue, found by continuing a search approach or designing a new one |
| `candidate` | lead → listed | New datasets in the inventory with first checks; duds ruled out for good |
| `read` | listed → verified | Unverified datasets verified from the publisher's page |
| `person-read` | listed → verified | Datasets on sites that block scripts, checked by you in your browser (almost no tokens) |
| `successor` | failed → listed or retired | Dead links repaired, or the dataset confirmed gone |
| `settle` | verified on thin evidence → verified in full | The missing checks filled in |
| `schema` | verified → fully specified | Column list, place key, its geography and vintage, geometry |
| a dataset you have in mind | nothing → listed | Give its name, its web address or DOI, or both. Claude finds it and confirms with you that it has the right one before going further, then tells you whether it is already in, and if not adds it with its checks (nothing to reserve) |

**`explore` is how new leads get found.** Choosing it shows the approaches tried so far (publisher fan-out, place-key search, targeted gap sweeps, DataCite by topic, priority-source listings): how each did, the verdict, and what's left. Pick one to continue from where it stopped, or work out a new one with Claude. You set the budget. You hand back new leads (which join the queue), any datasets read along the way, and a short note on how the approach performed. Without Claude: `python scripts/queue.py --approaches`.

Costs start from measured runs (`method/estimates.csv`) and update from what sessions here actually take: each ledger file's first line records items, minutes and fetches, and tokens if you give Claude your `/cost` total.

## Rules (Claude follows these; so should you)

- **Evidence URL for every value.** Not from memory, a search snippet or another AI. Unread means `not_checked`.
- **No sign-ins, registrations, form submissions, bot-check workarounds, or data-file downloads.** Blocked pages are recorded as blocked (and become `person-read` items).
- **Units from `method/unit-vocabulary.csv`.** If none fits, say so in the PR; don't invent one.
- **Person-level records stay out** (registries of named individuals and the like).
- **Ledger only.** Don't edit `base/`, `build/`, `method/`, `scripts/` or `.claude/` in a contribution PR; those need a maintainer's review (CODEOWNERS).

## Stopping early, and picking up again

- **Not sure where things stand?** `python scripts/status.py` (or `/inventory status`) shows what is saved on your computer and not yet submitted, your open reservations and how far along each is, and your pull requests still being checked. It changes nothing and uses no tokens, so it works even when your Claude allowance has run out.
- **Say "wrap up" at any point.** Claude finishes the item in hand, submits what's done, and the rest of what you reserved goes back to the queue.
- **If a session dies** (you hit a usage limit, the terminal closes), nothing is lost beyond the item in progress: Claude saves each item as it finishes. Next time you type `/inventory`, it finds the unfinished work and asks whether to submit it, continue it, or discard it.
- Claude can't see how much of your Claude allowance is left, so it can't stop by itself when you run low. Choose an amount you're comfortable with up front; the menu shows the token cost of each.

## What gets saved on your computer

Claude writes only inside your copy of this repository, and only these:

| Where | What | When it goes away |
|---|---|---|
| `ledger/<date>-<your-handle>-<name>.jsonl` | Your work in progress: one line per dataset finished, written as each one is done | It is submitted with your contribution and becomes part of the repository. Until then it exists only on your computer |
| `ledger/packets/`, `ledger/leads/`, `ledger/notes/` | Extra files for some kinds of work (a dataset's column list; leads found; a note on how an approach went) | Same as above |
| `.inventory-discarded/` | Work you chose to discard when recovering an unfinished session, kept in case you change your mind | Never submitted (git ignores it). Delete the folder whenever you like |

Nothing else is stored: no web pages, no downloaded data, no logs, and nothing outside this folder. Until you say yes to "Submit this?", nothing leaves your computer except the reservation itself (the `[claim]` issue on GitHub, opened when you agree to the list). Claude Code keeps its own record of your sessions, as it does for any project; that is separate from this repository.

## If CI fails

The pull request stays open with a red check; nothing is merged. Tell Claude "the check failed on my pull request" and it will fix it. The usual causes:

- **"was changed on origin/main since you branched"**: someone settled the same row first. Re-check that row against what's on `main` now (`python scripts/lookup.py --id <id>`), drop or update your record, `git rebase origin/main`, push again.
- **Anything else**: run `python scripts/validate.py --changed` locally; the message says which line and why.

## What happens after merge

CI replays the ledger, rebuilds `build/` (inventory, queue, site data), recomputes tiers and closes your claim. Your handle goes into each row's change note. A maintainer releases snapshots to the OHDSI GIS site.
