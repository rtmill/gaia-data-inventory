#!/usr/bin/env python3
"""Small, token-cheap lookups (run from the repo root). Use these instead of opening the big CSVs.

    python scripts/lookup.py "<name, DOI, URL or id>"   top matches in the inventory and the candidate families
    python scripts/lookup.py --id <id>                  the key fields of one row (add --all for every field)

For the work queue (what's open, slices, estimates, claiming) use scripts/queue.py.
"""
import csv, difflib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

B = inv.BUILD
CORE = ("chk_license", "chk_unit", "chk_temporal", "chk_access", "chk_join_key", "chk_format_gaia")
load = lambda p: list(csv.DictReader(open(p, encoding="utf-8-sig", newline="")))


def score(q, r, fields):
    qd, qt = inv.norm_doi(q), inv.norm_title(q)
    hay = " ".join(r.get(f, "") for f in fields)
    if q.strip().lower() == r.get("id", "").lower():
        return 1.0
    if qd and qd in inv.all_dois(hay):
        return 0.99
    if q.startswith("http"):
        u = q.lower().rstrip("/").split("://")[-1]
        if u and u in hay.lower():
            return 0.9
    t = inv.norm_title(r.get("dataset_name") or r.get("title") or "")
    s = difflib.SequenceMatcher(None, qt, t).ratio() if qt and t else 0
    if qt and all(w in t.split() for w in qt.split()):
        s = max(s, 0.8)
    return round(s, 2)


def search(q):
    rows = load(os.path.join(B, "inventory-all.csv"))
    f = ("id", "dataset_name", "organization", "site_url", "access_url", "persistent_id", "evidence_url", "notes")
    print(f"Inventory ({len(rows)} rows), best matches for {q!r}:")
    top = sorted(((score(q, r, f), r) for r in rows), key=lambda x: -x[0])[:5]
    if not any(s >= 0.4 for s, _ in top):
        print("  no match: nothing in the inventory resembles this")
    for s, r in top:
        if s >= 0.4:
            oc = ",".join(c[4:] for c in CORE if r.get(c) not in ("pass", "warn", "fail", "n.a.")) or "none"
            print(f"  {s:.2f}  {r['id']}  [{r['verify_tier']}]  {r['dataset_name'][:80]} | {r['organization'][:40]}\n"
                  f"        {r['site_url'][:100]}  unit={r.get('finest_unit_confirmed') or r.get('finest_unit', '')}  open checks: {oc}")
    fam = load(os.path.join(inv.ROOT, "base", "candidate-families.csv"))
    hits = [(s, r) for s, r in sorted(((score(q, r, ("doi", "all_dois", "title", "publisher")), r) for r in fam), key=lambda x: -x[0])[:3] if s >= 0.6]
    if hits:
        print("Candidate families (not yet checked):")
        for s, r in hits:
            print(f"  {s:.2f}  {r['doi']}  {r['title'][:80]} | {r['publisher'][:30]} | {r['anchors']} | {r['region']}")
    if any(s >= 0.4 for s, _ in top) or hits:
        print("A match >= 0.75 with the same publisher or DOI means it is already in: update that row.")


def one(i):
    for r in load(os.path.join(B, "inventory-all.csv")):
        if r["id"] == i:
            KEEP = ("id", "dataset_name", "organization", "site_url", "access_url", "verify_tier", "tier_cap", "verification_level", "license_confirmed", "license_class",
                    "temporal_confirmed", "finest_unit_confirmed", "access_confirmed", "join_key_confirmed", "formats_confirmed", "place_key_system", "place_key_vintage",
                    "schema_source", "region", "category", "persistent_id", "notes", inv.NOTE)
            for k, v in r.items():
                if v and ("--all" in sys.argv or k in KEEP or (k.startswith("chk_") and not k.endswith(("_detail", "_evidence")))):
                    print(f"{k}: {v[:200]}")
            if "--all" not in sys.argv:
                print("(key fields only; add --all for every field, including each check's detail and evidence)")
            return
    sys.exit(f"no row {i}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    {"--id": lambda: one(a[1])}.get(a[0], lambda: search(" ".join(a)))()
