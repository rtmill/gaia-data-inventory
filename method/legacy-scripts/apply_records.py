#!/usr/bin/env python3
"""Maintainer tool: apply change records to an inventory master and write a NEW master (never overwrites).

    python apply_records.py <src_master.csv> <out_master.csv> <records.jsonl> [--verified inventory.csv] [--date YYYY-MM-DD]

Same logic as the working copy (docs/discovery/scripts/apply_records_2026_11_02.py in the Gaia workspace), with paths
taken as given, contributor handles kept in the row note, and an optional `tier_cap` column honoured:
if a row has tier_cap (e.g. "Silver: geometry dependency TBD"), its computed tier is never above that tier.

Record format, one JSON object per line:
  {"id", "new"?: true, "set": {column: value}, "ev": "<evidence URL>", "note": "...", "by"?: "<handle>", "packet"?, "batch"?}
Only rows whose record sets a check (chk_*, url_health, browser_tier) or that are new are re-tiered; label-only edits keep
their tier. Writes <out_master>, the verified list (Gold + Silver) if --verified is given, and <records>-tier-moves.csv.
Run validate.py on contributor files first.
"""
import argparse, csv, datetime, json, os
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("records")
ap.add_argument("--verified"); ap.add_argument("--date", default=datetime.date.today().isoformat())
a = ap.parse_args()
assert not os.path.exists(a.out), f"{a.out} exists; never overwrite a master"
NOTE = "run_2026_11_02_note"   # the row's latest-change note (historical column name, kept for continuity)
CHECKS_A = ["chk_link_live", "chk_redirect", "chk_tls", "chk_soft404", "chk_withdrawn", "chk_access_url", "chk_format_match",
            "chk_machine_metadata", "chk_persistent_id", "chk_archived"]
B_CHECKS = ["chk_license", "chk_temporal", "chk_recency", "chk_cadence", "chk_version", "chk_unit", "chk_coverage", "chk_access",
            "chk_join_key", "chk_format_gaia"]
ALL = CHECKS_A + B_CHECKS + ["chk_in_gaia", "chk_recipe_health"]
WEIGHTS = {"chk_link_live": 20, "chk_soft404": 10, "chk_withdrawn": 10, "chk_license": 15, "chk_unit": 15, "chk_temporal": 7.5,
           "chk_recency": 7.5, "chk_access": 10, "chk_join_key": 10, "chk_machine_metadata": 5}
VAL = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
RANK = ["Failed", "Browser needed", "Bronze", "Silver", "Gold"]


def summarise(r):
    app = [c for c in ALL if r.get(c) in VAL]
    r["checks_applicable"] = len(app); r["checks_passed"] = sum(r[c] == "pass" for c in app)
    r["checks_warned"] = sum(r[c] == "warn" for c in app); r["checks_failed"] = sum(r[c] == "fail" for c in app)
    w = sum(WEIGHTS[c] for c in app if c in WEIGHTS)
    r["health_score"] = round(100 * sum(WEIGHTS[c] * VAL[r[c]] for c in app if c in WEIGHTS) / w) if w else ""
    r["all_passing"] = "TRUE" if app and r["checks_passed"] == len(app) else "FALSE"
    r["verify_blockers"] = ";".join([c[4:] for c in ALL if r.get(c) == "fail"] + [c[4:] + "(warn)" for c in ALL if r.get(c) == "warn"])


def tier_of(r, b_done):
    ll = r["chk_link_live"]
    if r["url_health"] == "blocked": t = "Browser needed"
    elif ll == "fail" or r["chk_withdrawn"] == "fail" or r["chk_soft404"] == "fail" or r["chk_recency"] == "fail": t = "Failed"
    elif all(r[c] == "pass" for c in ("chk_link_live", "chk_soft404", "chk_withdrawn", "chk_license", "chk_unit", "chk_temporal", "chk_access")) \
            and r["chk_recency"] in ("pass", "warn"): t = "Gold"
    elif ll == "pass" and b_done and not any(r[c] == "fail" for c in ("chk_license", "chk_unit", "chk_temporal", "chk_recency")): t = "Silver"
    elif ll in ("pass", "warn", "n.a."): t = "Bronze"
    else: t = "Failed"
    if r.get("browser_tier"): t = r["browser_tier"]
    cap = (r.get("tier_cap") or "").split(":")[0].strip()
    if cap in RANK and t in RANK and RANK.index(t) > RANK.index(cap): t = cap
    return t


rows = list(csv.DictReader(open(a.src, encoding="utf-8-sig", newline=""))); cols = list(rows[0].keys())
for c in (NOTE,):
    if c not in cols: cols.append(c)
for r in rows:
    for c in cols: r.setdefault(c, "")
by = {r["id"]: r for r in rows}
recs = [json.loads(l) for l in open(a.records, encoding="utf-8") if l.strip()]
step = os.path.splitext(os.path.basename(a.records))[0]
before = {r["id"]: r["verify_tier"] for r in rows}
for x in recs:
    if x.get("new"):
        assert x["id"] not in by, f"{x['id']} already exists"
        r = {c: "" for c in cols}; r["id"] = x["id"]; rows.append(r); by[x["id"]] = r; before[x["id"]] = "(new)"
    r = by[x["id"]]
    bad = [k for k in x.get("set", {}) if k not in cols]
    assert not bad, f"unknown columns {bad}"
    for k, v in x.get("set", {}).items(): r[k] = v
    who = f" by {x['by']}" if x.get("by") else ""
    r[NOTE] = f"{step} {a.date}{who}: {x.get('note', '')}" + (f"; evidence {x['ev']}" if x.get("ev") else "")
    # A schema/metadata record is not a page verification (it carries schema_source): no verified_on / partB_* stamp.
    if x.get("ev") and x.get("verifies", "schema_source" not in x.get("set", {})):
        r["partB_pages_read"] = (r["partB_pages_read"] + "; " if r["partB_pages_read"] else "") + x["ev"]
        r["partB_source"] = (r["partB_source"] + "; " if r["partB_source"] else "") + step
        r["verified_on"] = a.date
ids = {x["id"] for x in recs if x.get("new") or any(k.startswith("chk_") or k in ("url_health", "browser_tier") for k in x.get("set", {}))}
for r in rows:
    summarise(r)
    if r["id"] in ids:
        r["verify_tier"] = tier_of(r, any(r[c] in VAL for c in B_CHECKS))
        if r["verify_tier"] in ("Gold", "Silver") and not r.get("verification_level", "").startswith("file"):
            r["verification_level"] = "page-verified"
        r["tier"] = r["verify_tier"]
w = csv.DictWriter(open(a.out, "w", newline="", encoding="utf-8"), fieldnames=cols); w.writeheader(); w.writerows(rows)
if a.verified:
    ic = list(csv.DictReader(open(a.verified, encoding="utf-8-sig")).fieldnames)
    w = csv.DictWriter(open(a.verified, "w", newline="", encoding="utf-8"), fieldnames=ic, extrasaction="ignore"); w.writeheader()
    for r in rows:
        if r["verify_tier"] in ("Gold", "Silver") and r.get("round") != "2-pilot": w.writerow({c: r.get(c, "") for c in ic})
moves = os.path.splitext(a.records)[0] + "-tier-moves.csv"
with open(moves, "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f); cw.writerow(["id", "tier_before", "tier_after", "by", "note"])
    for x in recs: cw.writerow([x["id"], before[x["id"]], by[x["id"]]["verify_tier"], x.get("by", ""), x.get("note", "")])
K = [r for r in rows if r.get("round") != "2-pilot"]
T = lambda rs: {k: Counter(rs)[k] for k in RANK[::-1]}
print("rows", len(rows), "| before", T([before[r["id"]] for r in K if before[r["id"]] != "(new)"]), "| after", T([r["verify_tier"] for r in K]))
for x in recs: print(" ", x["id"], before[x["id"]], "->", by[x["id"]]["verify_tier"])
