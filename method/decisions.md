# Decisions on record

Policy and method decisions that shape the inventory, newest first. Open questions for the working group are in `TODO.md` (tier 4).

- **2026-11-18 (Robert): the inventory moves to this repo.** Base = the workspace master after iteration #25 (p7c); every change since is a ledger file. Contributors write ledger files; CI rebuilds; maintainers release snapshots to OHDSI/GIS.
- **2026-11-18 (Robert): a schema or metadata read is not a page verification.** Records that set `schema_source` don't stamp `verified_on` or `partB_*` (after #25).
- **2026-11-18 (Robert): the schema pass reads metadata only** (no sample rows, value coding or downloads).
- **2026-11-03 (Robert): only the Miami-Dade datasets from the existing gaiaCatalog are first-class;** Miami-Dade layers found later get no special treatment.
- **2026-11-02 (Robert): federal-rule edge cases are settled by a page read only** (labs, DAACs, Smithsonian, multi-provider portals).
- **2026-11-02 (Robert): ZIP to ZCTA uses the archived UDS crosswalk.**
- **2026-11-02 (Robert): tightening Silver (TODO 4.10) goes to the WG;** no change until then.
- **2026-10-29: US federal rule.** A US federal publisher on a .gov page counts as a licence pass (`public_domain_us_federal`, 17 U.S.C. 105) unless the page states other terms.
- **2026-10-22: recency cut-off.** Data ending before 2000 fails recency.
- **2026-10-20 (Robert): broad harvest first, then curation;** the end goal stays a curated, health-relevant inventory.
