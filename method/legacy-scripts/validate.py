#!/usr/bin/env python3
"""Check contributor change records before a maintainer applies them (run from exploration/place-data-inventory/).

    python method/scripts/validate.py contrib/<file>.jsonl [more files]

Exit 1 on any error. Warnings don't block, but the maintainer reads them.
"""
import csv, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lookup import load, score  # noqa: E402

rows = load(os.path.join(ROOT, "inventory-all.csv"))
COLS = set(rows[0].keys())
IDS = {r["id"]: r for r in rows}
UNITS = {r["term"].strip() for r in load(os.path.join(ROOT, "method", "unit-vocabulary.csv"))}
LIC = {"open", "attribution", "non-commercial", "registration", "restricted", "unknown", "public_domain_us_federal"}
VOCAB = {"pass", "warn", "fail", "n.a.", "not_checked"}
COMPUTED = {"verify_tier", "tier", "browser_tier", "health_score", "checks_applicable", "checks_passed", "checks_warned",
            "checks_failed", "all_passing", "verify_blockers", "verified_on", "partB_pages_read", "partB_source", "run_2026_11_02_note"}
NEW_REQ = ("dataset_name", "organization", "site_url", "category", "region")
URL = re.compile(r"^https?://\S+")
PACKET_KEYS = ("schema_source", "columns", "place_key", "geometry", "sample_rows", "value_coding", "missing_coding", "evidence")

errs, warns = [], []
E = lambda f, n, m: errs.append(f"{f}:{n}: {m}")
W = lambda f, n, m: warns.append(f"{f}:{n}: {m}")

for path in sys.argv[1:]:
    fn = os.path.basename(path)
    if not re.match(r"^\d{4}-\d{2}-\d{2}-[A-Za-z0-9-]+-[a-z0-9-]+\.jsonl$", fn):
        W(fn, 0, "name should be <YYYY-MM-DD>-<handle>-<slug>.jsonl")
    seen = set()
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            x = json.loads(line)
        except json.JSONDecodeError as e:
            E(fn, n, f"not JSON: {e}")
            continue
        i = x.get("id", "")
        for k in ("id", "by", "packet", "ev", "note"):
            if not x.get(k):
                E(fn, n, f"missing '{k}'")
        if x.get("packet") not in ("a", "b", "c", "d"):
            E(fn, n, "packet must be a, b, c or d")
        if x.get("ev") and not all(URL.match(u.strip()) for u in x["ev"].split(";") if u.strip()):
            E(fn, n, "ev must be one or more URLs separated by ';'")
        if i in seen:
            E(fn, n, f"{i} appears twice in this file")
        seen.add(i)
        s = x.get("set", {})
        if x.get("new"):
            if x.get("packet") != "a":
                E(fn, n, "new rows only in packet a")
            if i in IDS:
                E(fn, n, f"{i} already exists; drop 'new' and update it")
            if not re.match(r"^[a-z0-9]+(_[a-z0-9.]+)+$", i):
                E(fn, n, "id should be <country>_<publisher>_<product>, lowercase with underscores")
            for k in NEW_REQ:
                if not s.get(k):
                    E(fn, n, f"new row needs '{k}'")
            q = s.get("dataset_name", "")
            best = max(((score(q, r, ("dataset_name", "organization", "site_url", "persistent_id")), r["id"]) for r in rows), default=(0, ""))
            if best[0] >= 0.75:
                W(fn, n, f"possible duplicate of {best[1]} (score {best[0]})")
            if s.get("round", "contrib") != "contrib":
                E(fn, n, "new rows use round = contrib")
        elif i and i not in IDS:
            E(fn, n, f"unknown id {i}")
        for k, v in s.items():
            if k not in COLS:
                E(fn, n, f"unknown column {k}")
            if k in COMPUTED:
                E(fn, n, f"{k} is computed by the apply script; don't set it")
            if re.fullmatch(r"chk_[a-z0-9_]+", k) and not k.endswith(("_detail", "_evidence")):
                if v not in VOCAB:
                    E(fn, n, f"{k} = {v!r}; use pass/warn/fail/n.a./not_checked")
                if v in ("pass", "warn", "fail"):
                    evk = k + "_evidence"
                    if evk in COLS and not s.get(evk) and not x.get("ev"):
                        E(fn, n, f"{k} set without {evk} or ev")
                    if k + "_detail" in COLS and not s.get(k + "_detail"):
                        W(fn, n, f"{k} has no {k}_detail")
            if k.endswith("_evidence") and v and not all(URL.match(u.strip()) for u in v.split(";") if u.strip()):
                E(fn, n, f"{k} must be URLs")
        if s.get("finest_unit_confirmed"):
            for u in re.split(r"[;,]\s*", s["finest_unit_confirmed"]):
                if u and u not in UNITS and not re.fullmatch(r"grid_[0-9.]+(m|km|deg)", u):
                    E(fn, n, f"unit {u!r} not in method/unit-vocabulary.csv")
        if s.get("license_class") and s["license_class"] not in LIC:
            E(fn, n, f"license_class {s['license_class']!r} not one of {sorted(LIC)}")
        if s.get("license_class") == "public_domain_us_federal":
            evs = (s.get("chk_license_evidence", "") + ";" + x.get("ev", "")).lower()
            if ".gov" not in evs:
                E(fn, n, "federal rule needs a .gov evidence page")
        if x.get("packet") == "c":
            p = os.path.join(os.path.dirname(os.path.abspath(path)), "packets", f"{i}.json")
            if not os.path.exists(p):
                E(fn, n, f"packet c needs contrib/packets/{i}.json")
            else:
                try:
                    pk = json.load(open(p, encoding="utf-8"))
                    miss = [k for k in PACKET_KEYS if k not in pk]
                    if miss:
                        E(fn, n, f"packets/{i}.json missing {miss}")
                    pkk = pk.get("place_key", {}) if isinstance(pk.get("place_key"), dict) else {}
                    if not (pkk.get("system") and pkk.get("vintage")):
                        W(fn, n, f"packets/{i}.json: place_key system or vintage missing")
                except json.JSONDecodeError as e:
                    E(fn, n, f"packets/{i}.json not JSON: {e}")

for w in warns:
    print("warn ", w)
for e in errs:
    print("ERROR", e)
print(f"{len(errs)} errors, {len(warns)} warnings")
sys.exit(1 if errs else 0)
