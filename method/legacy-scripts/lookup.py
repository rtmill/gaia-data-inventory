#!/usr/bin/env python3
"""Small, token-cheap lookups into the place-data inventory (run from exploration/place-data-inventory/).

    python method/scripts/lookup.py "<name, DOI, URL or id>"   top matches in the inventory and the candidate pool
    python method/scripts/lookup.py --id <id>                  every non-empty field of one row
    python method/scripts/lookup.py --batch <BATCH>            the rows of one queue batch (e.g. BR-03)
    python method/scripts/lookup.py --queues                   queue files and their batches

Matching is never exact-DOI only: DOIs are normalised (case, resolver prefix, version suffixes), ICPSR study
numbers are compared, and titles are fuzzy-matched.
"""
import csv, difflib, glob, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
INV = os.path.join(ROOT, "inventory-all.csv")
CAND = os.path.join(ROOT, "candidates-unvalidated.csv")
QDIR = os.path.join(ROOT, "queues")
CORE = ("chk_license", "chk_unit", "chk_temporal", "chk_access", "chk_join_key", "chk_format_gaia")
SETTLED = ("pass", "warn", "fail", "n.a.")


def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm_doi(s):
    s = (s or "").lower().strip()
    m = re.search(r"10\.\d{4,9}/[^\s;,\"']+", s)
    if not m:
        return ""
    d = m.group(0).rstrip(".")
    return re.sub(r"(\.v\d+|/v\d+|v\d+-\d+|\.\d{1,2})$", "", d)   # version suffixes: .v2, /v1, v1-189241, Mendeley .1


def all_dois(s):
    return {norm_doi(m) for m in re.findall(r"10\.\d{4,9}/[^\s;,\"']+", (s or "").lower())}


def icpsr(s):
    m = re.search(r"icpsr\s*0*(\d{4,6})|openicpsr[^\d]*(\d{5,6})", (s or "").lower())
    return (m.group(1) or m.group(2)) if m else ""


def norm_title(s):
    s = re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())
    return " ".join(w for w in s.split() if w not in {"the", "of", "and", "a", "an", "for", "in", "data", "dataset"})


def open_checks(r):
    return [c[4:] for c in CORE if r.get(c, "") not in SETTLED]


def score(q, r, fields):
    qd, qi, qt = norm_doi(q), icpsr(q), norm_title(q)
    hay = " ".join(r.get(f, "") for f in fields)
    if q.strip().lower() == r.get("id", "").lower():
        return 1.0
    if qd and qd in all_dois(hay):
        return 0.99
    if qi and qi == icpsr(hay):
        return 0.95
    if q.startswith("http"):
        u = q.lower().rstrip("/").split("://")[-1]
        if u and u in hay.lower():
            return 0.9
    t = norm_title(r.get("dataset_name") or r.get("title") or "")
    s = difflib.SequenceMatcher(None, qt, t).ratio() if qt and t else 0
    if qt and all(w in t for w in qt.split()):
        s = max(s, 0.8)
    return round(s, 2)


def search(q):
    rows = load(INV)
    f = ("id", "dataset_name", "organization", "site_url", "access_url", "persistent_id", "evidence_url", "notes")
    hits = sorted(((score(q, r, f), r) for r in rows), key=lambda x: -x[0])[:5]
    print(f"Inventory ({len(rows)} rows), top matches for {q!r}:")
    for s, r in hits:
        if s < 0.4:
            continue
        oc = ",".join(open_checks(r)) or "none"
        print(f"  {s:.2f}  {r['id']}  [{r['verify_tier']}]  {r['dataset_name'][:80]} | {r['organization'][:40]}")
        print(f"        {r['site_url'][:100]}  unit={r.get('finest_unit_confirmed') or r.get('finest_unit','')}  open checks: {oc}")
    if os.path.exists(CAND):
        c = load(CAND)
        ch = sorted(((score(q, r, ("doi", "title", "publisher", "url")), r) for r in c), key=lambda x: -x[0])[:3]
        ch = [(s, r) for s, r in ch if s >= 0.6]
        if ch:
            print("Candidate pool (unvalidated):")
            for s, r in ch:
                print(f"  {s:.2f}  {r['doi']}  {r['title'][:80]} | {r['publisher'][:30]} | triage={r['triage']} in_inventory={r['in_inventory']}")
    print("Score >= 0.75 with the same publisher or DOI root: treat as already in (update that row).")


def one(i):
    for r in load(INV):
        if r["id"] == i:
            for k, v in r.items():
                if v:
                    print(f"{k}: {v[:300]}")
            return
    sys.exit(f"no row {i}")


def batch(b):
    n = 0
    for p in sorted(glob.glob(os.path.join(QDIR, "*.csv"))):
        for r in load(p):
            if r["batch"] == b:
                n += 1
                print(f"{r['id']}  [{r['verify_tier']}]  {r['dataset_name'][:70]}\n    {r['site_url']}\n    open: {r['open_checks']}  hint: {r['hint'][:160]}")
    if not n:
        sys.exit(f"no batch {b}")


def queues():
    for p in sorted(glob.glob(os.path.join(QDIR, "*.csv"))):
        rows = load(p)
        bs = sorted({r["batch"] for r in rows})
        print(f"{os.path.basename(p)}: {len(rows)} rows, batches {bs[0]}..{bs[-1]} ({len(bs)})" if bs else f"{os.path.basename(p)}: empty")
    print("Claims are on the tracker issue; check it before starting a batch.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--id":
        one(a[1])
    elif a[0] == "--batch":
        batch(a[1])
    elif a[0] == "--queues":
        queues()
    else:
        search(" ".join(a))
