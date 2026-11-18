#!/usr/bin/env python3
"""Small, token-cheap lookups (run from the repo root). Use these instead of opening the big CSVs.

    python scripts/lookup.py "<name, DOI, URL or id>"   top matches in the inventory and the candidate families
    python scripts/lookup.py --id <id>                  every non-empty field of one row
    python scripts/lookup.py --batch <BATCH>            the rows (or candidates) of one batch, e.g. BR-03 or CA-02
    python scripts/lookup.py --batches                  open batches per queue
"""
import csv, difflib, glob, json, os, sys
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
    for s, r in sorted(((score(q, r, f), r) for r in rows), key=lambda x: -x[0])[:5]:
        if s >= 0.4:
            oc = ",".join(c[4:] for c in CORE if r.get(c) not in ("pass", "warn", "fail", "n.a.")) or "none"
            print(f"  {s:.2f}  {r['id']}  [{r['verify_tier']}]  {r['dataset_name'][:80]} | {r['organization'][:40]}\n"
                  f"        {r['site_url'][:100]}  unit={r.get('finest_unit_confirmed') or r.get('finest_unit', '')}  open checks: {oc}")
    fam = load(os.path.join(inv.ROOT, "base", "candidate-families.csv"))
    hits = [(s, r) for s, r in sorted(((score(q, r, ("doi", "all_dois", "title", "publisher")), r) for r in fam), key=lambda x: -x[0])[:3] if s >= 0.6]
    if hits:
        print("Candidate families (not yet checked unless in a closed batch):")
        for s, r in hits:
            print(f"  {s:.2f}  {r['doi']}  {r['title'][:80]} | {r['publisher'][:30]} | {r['anchors']} | {r['region']}")
    print("A match >= 0.75 with the same publisher or DOI means it is already in: update that row.")


def one(i):
    for r in load(os.path.join(B, "inventory-all.csv")):
        if r["id"] == i:
            for k, v in r.items():
                if v:
                    print(f"{k}: {v[:300]}")
            return
    sys.exit(f"no row {i}")


def batch(b):
    for p in sorted(glob.glob(os.path.join(B, "queues", "*.csv"))):
        rs = [r for r in load(p) if r.get("batch") == b]
        for r in rs:
            if "doi" in r:
                print(f"{r['doi']}  {r['title'][:90]}\n    publisher {r['publisher']} | {r['year']} | anchors {r['anchors']} | region {r['region']} | siblings {r['siblings']}")
            else:
                print(f"{r['id']}  [{r['verify_tier']}]  {r['dataset_name'][:80]}\n    {r['site_url']}\n    open: {r['open_checks']}  hint: {r['hint'][:160]}")
        if rs:
            print(f"({len(rs)} items, packet {rs[0]['packet']}, queue {os.path.basename(p)[:-4]})")
            return
    sys.exit(f"no open batch {b}")


def batches():
    bj = json.load(open(os.path.join(B, "batches.json"), encoding="utf-8"))["batches"]
    by = {}
    for bid, x in sorted(bj.items()):
        if x["status"] == "open":
            by.setdefault(x["queue"], []).append(bid)
    for q, ids in by.items():
        print(f"{q}: {len(ids)} open ({', '.join(ids[:6])}{' ...' if len(ids) > 6 else ''})")
    print("Claim one by assigning yourself its GitHub issue ([batch XX-nn]).")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    {"--id": lambda: one(a[1]), "--batch": lambda: batch(a[1]), "--batches": batches}.get(a[0], lambda: search(" ".join(a)))()
