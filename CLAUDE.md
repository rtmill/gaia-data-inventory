# Gaia data inventory

An evidence-backed inventory of public geospatial datasets for linking place to health, assessed for Gaia (OHDSI GIS WG). `README.md` explains the layout (base + ledger = build).

**Default mode is contributor mode.** When the user types `/inventory`, "inventory: start", gives a claim issue number, asks for work from the queue ("20 candidates in Africa"), or asks to help with the inventory, use the `inventory` skill. Maintainer work (reviewing PRs, method changes, releases to OHDSI/GIS) uses `inventory-maintainer`.

Always:

- **Never read `build/inventory-all.csv`, `base/inventory-base.csv` or `base/candidates-datacite-*.csv` into context.** They are large. Use `python scripts/queue.py` (the work queue) and `python scripts/lookup.py` (find a row).
- **Contributions write only `ledger/<YYYY-MM-DD>-<handle>-<slug>.jsonl`** (plus `ledger/packets/<id>.json` for packet c). Never edit `base/`, `build/`, `method/`, `scripts/`, `.claude/` or `.github/` unless the user is a maintainer and asks.
- **Evidence URL for every value**, read from the publisher's page, a repository or catalog record (Zenodo, figshare, Dataverse, CKAN, Socrata, ArcGIS JSON) or a metadata record. Your own knowledge of a dataset is not evidence. Search results are not evidence.
- **No sign-ins, registrations, form submissions, bot-check workarounds or data-file downloads.** Record blocked pages as blocked.
- **Caps** in the skill apply. When one is hit, stop and write what you have.
- Commit or push only when the user asks. Never add AI attribution (co-author trailers, "generated with" lines, session links) to commits, PRs, issues or files.
