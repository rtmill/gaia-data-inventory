#!/usr/bin/env python3
"""Apply one step's records (run-2026-11-02/<step>.jsonl) to a master and write a new master.
    python scripts/apply_records_2026_11_02.py <src_master> <out_master> <records.jsonl | step> [date]     (run from docs/discovery)

Pattern: scripts/apply_browser_pass_2026_10_30.py (same summarise() / tier_of(), imported from it by copy).
Record format, one JSON object per line:
  {"id": ..., "new": true|false, "template": <id to copy blank columns from, new rows only>,
   "set": {column: value, ...},      # plain field overwrites (values from a page read; evidence in *_evidence or ev)
   "ev": "<evidence URL>", "note": "<what was read and why>"}
Only rows whose record sets a check (chk_*, url_health, browser_tier) or that are new are re-tiered; label-only edits keep their tier. Old masters are never overwritten (refuses if out exists).
Outputs: <out_master>, inventory.csv (Gold + Silver), run-2026-11-02/<step>-tier-moves.csv
"""
import csv, json, os, sys
from collections import Counter
D = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = lambda p: os.path.join(D, p)
SRC, OUT, STEP = sys.argv[1], sys.argv[2], sys.argv[3]; TODAY = sys.argv[4] if len(sys.argv) > 4 else __import__("datetime").date.today().isoformat()
assert not os.path.exists(P(OUT)), f"{OUT} exists; never overwrite a master"
CHECKS_ALL = ["chk_link_live", "chk_redirect", "chk_tls", "chk_soft404", "chk_withdrawn", "chk_access_url", "chk_format_match",
              "chk_machine_metadata", "chk_persistent_id", "chk_archived"]
B_CHECKS = ["chk_license", "chk_temporal", "chk_recency", "chk_cadence", "chk_version", "chk_unit", "chk_coverage", "chk_access", "chk_join_key", "chk_format_gaia"]
ALL_CHECKS = CHECKS_ALL + B_CHECKS + ["chk_in_gaia", "chk_recipe_health"]
WEIGHTS = {"chk_link_live": 20, "chk_soft404": 10, "chk_withdrawn": 10, "chk_license": 15, "chk_unit": 15, "chk_temporal": 7.5, "chk_recency": 7.5,
           "chk_access": 10, "chk_join_key": 10, "chk_machine_metadata": 5}
VAL = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
def summarise(r):
    app = [c for c in ALL_CHECKS if r.get(c) in VAL]
    r["checks_applicable"] = len(app); r["checks_passed"] = sum(1 for c in app if r[c] == "pass")
    r["checks_warned"] = sum(1 for c in app if r[c] == "warn"); r["checks_failed"] = sum(1 for c in app if r[c] == "fail")
    wsum = sum(WEIGHTS[c] for c in app if c in WEIGHTS)
    r["health_score"] = round(100 * sum(WEIGHTS[c] * VAL[r[c]] for c in app if c in WEIGHTS) / wsum) if wsum else ""
    r["all_passing"] = "TRUE" if app and r["checks_passed"] == len(app) else "FALSE"
    r["verify_blockers"] = ";".join([c[4:] for c in ALL_CHECKS if r.get(c) == "fail"] + [c[4:] + "(warn)" for c in ALL_CHECKS if r.get(c) == "warn"])
def tier_of(r, b_done):
    ll = r["chk_link_live"]
    if r["url_health"] == "blocked": t = "Browser needed"
    elif ll == "fail" or r["chk_withdrawn"] == "fail" or r["chk_soft404"] == "fail" or r["chk_recency"] == "fail": t = "Failed"
    elif all(r[c] == "pass" for c in ("chk_link_live", "chk_soft404", "chk_withdrawn", "chk_license", "chk_unit", "chk_temporal", "chk_access")) and r["chk_recency"] in ("pass", "warn"): t = "Gold"
    elif ll == "pass" and b_done and not any(r[c] == "fail" for c in ("chk_license", "chk_unit", "chk_temporal", "chk_recency")): t = "Silver"
    elif ll in ("pass", "warn", "n.a."): t = "Bronze"
    else: t = "Failed"
    if r.get("browser_tier"): t = r["browser_tier"]
    return t
rows = list(csv.DictReader(open(P(SRC), encoding="utf-8-sig"))); cols = list(rows[0].keys())
if "run_2026_11_02_note" not in cols: cols.append("run_2026_11_02_note")
for r in rows:
    for c in cols: r.setdefault(c, "")
by = {r["id"]: r for r in rows}
REC = STEP if STEP.endswith(".jsonl") else f"run-2026-11-02/{STEP}.jsonl"   # a path ending in .jsonl (relative to docs/discovery) or a step name in run-2026-11-02
STEPNAME = os.path.splitext(os.path.basename(REC))[0]; MOVES = os.path.join(os.path.dirname(REC), STEPNAME + "-tier-moves.csv")
recs = [json.loads(l) for l in open(P(REC), encoding="utf-8") if l.strip()]
before = {r["id"]: r["verify_tier"] for r in rows}
for x in recs:
    if x.get("new"):
        assert x["id"] not in by, f"{x['id']} already exists"
        r = {c: "" for c in cols}; r["id"] = x["id"]; rows.append(r); by[x["id"]] = r; before[x["id"]] = "(new)"
    r = by[x["id"]]
    bad = [k for k in x.get("set", {}) if k not in cols]
    assert not bad, f"unknown columns {bad}"
    for k, v in x.get("set", {}).items(): r[k] = v
    r["run_2026_11_02_note"] = f"{STEPNAME} {TODAY}: {x.get('note','')}" + (f"; evidence {x['ev']}" if x.get("ev") else "")
    # A schema/metadata record is not a page verification: it carries its URL in schema_source and must not
    # stamp verified_on or partB_* (fix 2026-11-18 after P7). Opt out explicitly with "verifies": false.
    if x.get("ev") and x.get("verifies", "schema_source" not in x.get("set", {})):
        r["partB_pages_read"] = (r["partB_pages_read"] + "; " if r["partB_pages_read"] else "") + x["ev"]
        r["partB_source"] = (r["partB_source"] + "; " if r["partB_source"] else "") + STEPNAME
        r["verified_on"] = TODAY
ids = {x["id"] for x in recs if x.get("new") or any(k.startswith("chk_") or k in ("url_health", "browser_tier") for k in x.get("set", {}))}  # re-tier only when a check changed
for r in rows:
    summarise(r)
    if r["id"] in ids:
        b_done = any(r[c] in VAL for c in B_CHECKS)
        r["verify_tier"] = tier_of(r, b_done)
        if r["verify_tier"] in ("Gold", "Silver") and not r.get("verification_level", "").startswith("file"): r["verification_level"] = "page-verified"
        r["tier"] = r["verify_tier"]
w = csv.DictWriter(open(P(OUT), "w", newline="", encoding="utf-8"), fieldnames=cols); w.writeheader(); w.writerows(rows)
ic = list(csv.DictReader(open(P("inventory.csv"), encoding="utf-8-sig")).fieldnames)
w = csv.DictWriter(open(P("inventory.csv"), "w", newline="", encoding="utf-8"), fieldnames=ic, extrasaction="ignore"); w.writeheader()
for r in rows:
    if r["verify_tier"] in ("Gold", "Silver") and r.get("round") != "2-pilot": w.writerow({c: r.get(c, "") for c in ic})
with open(P(MOVES), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f); cw.writerow(["id", "tier_before", "tier_after", "note"])
    for x in recs: cw.writerow([x["id"], before[x["id"]], by[x["id"]]["verify_tier"], x.get("note", "")])
K = [r for r in rows if r.get("round") != "2-pilot"]
T = lambda rs: {k: Counter(rs)[k] for k in ("Gold", "Silver", "Bronze", "Browser needed", "Failed")}
print("rows", len(rows), "| before", T([before[r["id"]] for r in K if before[r["id"]] != "(new)"]), "| after", T([r["verify_tier"] for r in K]))
for x in recs: print(" ", x["id"], before[x["id"]], "->", by[x["id"]]["verify_tier"])
