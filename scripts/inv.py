"""Shared logic for the Gaia data inventory: loading, tiers, applying ledger records, replaying the ledger.

Everything here is deterministic: the same base plus the same ledger files give the same inventory.
Standard library only (Python 3.9+).
"""
import csv, glob, json, os, re
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BASE = os.path.join(ROOT, "base", "inventory-base.csv")
LEDGER = os.path.join(ROOT, "ledger")
BUILD = os.path.join(ROOT, "build")
NOTE = "run_2026_11_02_note"   # the row's latest-change note (historical column name, kept for continuity)

CHECKS_A = ["chk_link_live", "chk_redirect", "chk_tls", "chk_soft404", "chk_withdrawn", "chk_access_url", "chk_format_match",
            "chk_machine_metadata", "chk_persistent_id", "chk_archived"]
B_CHECKS = ["chk_license", "chk_temporal", "chk_recency", "chk_cadence", "chk_version", "chk_unit", "chk_coverage", "chk_access",
            "chk_join_key", "chk_format_gaia"]
ALL_CHECKS = CHECKS_A + B_CHECKS + ["chk_in_gaia", "chk_recipe_health"]
WEIGHTS = {"chk_link_live": 20, "chk_soft404": 10, "chk_withdrawn": 10, "chk_license": 15, "chk_unit": 15, "chk_temporal": 7.5,
           "chk_recency": 7.5, "chk_access": 10, "chk_join_key": 10, "chk_machine_metadata": 5}
VAL = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
RANK = ["Failed", "Browser needed", "Bronze", "Silver", "Gold"]
TIERS = RANK[::-1]
COMPUTED = {"verify_tier", "tier", "health_score", "checks_applicable", "checks_passed", "checks_warned", "checks_failed",
            "all_passing", "verify_blockers", "verified_on", "partB_pages_read", "partB_source", NOTE}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd), list(rd.fieldnames)


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def summarise(r):
    app = [c for c in ALL_CHECKS if r.get(c) in VAL]
    r["checks_applicable"] = str(len(app))
    r["checks_passed"] = str(sum(r[c] == "pass" for c in app))
    r["checks_warned"] = str(sum(r[c] == "warn" for c in app))
    r["checks_failed"] = str(sum(r[c] == "fail" for c in app))
    w = sum(WEIGHTS[c] for c in app if c in WEIGHTS)
    r["health_score"] = str(round(100 * sum(WEIGHTS[c] * VAL[r[c]] for c in app if c in WEIGHTS) / w)) if w else ""
    r["all_passing"] = "TRUE" if app and all(r[c] == "pass" for c in app) else "FALSE"
    r["verify_blockers"] = ";".join([c[4:] for c in ALL_CHECKS if r.get(c) == "fail"] + [c[4:] + "(warn)" for c in ALL_CHECKS if r.get(c) == "warn"])


def tier_of(r):
    """Tier rules (unchanged since 2026-10-30). A `tier_cap` column, if present, is a ceiling: "Silver: reason"."""
    b_done = any(r.get(c) in VAL for c in B_CHECKS)
    ll = r.get("chk_link_live", "")
    if r.get("url_health") == "blocked": t = "Browser needed"
    elif ll == "fail" or r.get("chk_withdrawn") == "fail" or r.get("chk_soft404") == "fail" or r.get("chk_recency") == "fail": t = "Failed"
    elif all(r.get(c) == "pass" for c in ("chk_link_live", "chk_soft404", "chk_withdrawn", "chk_license", "chk_unit", "chk_temporal", "chk_access")) \
            and r.get("chk_recency") in ("pass", "warn"): t = "Gold"
    elif ll == "pass" and b_done and not any(r.get(c) == "fail" for c in ("chk_license", "chk_unit", "chk_temporal", "chk_recency")): t = "Silver"
    elif ll in ("pass", "warn", "n.a."): t = "Bronze"
    else: t = "Failed"
    if r.get("browser_tier"): t = r["browser_tier"]
    cap = (r.get("tier_cap") or "").split(":")[0].strip()
    if cap in RANK and t in RANK and RANK.index(t) > RANK.index(cap): t = cap
    return t


def ledger_files():
    """Ledger files in apply order: by file name (which starts with the date)."""
    return sorted(glob.glob(os.path.join(LEDGER, "*.jsonl")))


def file_date(path):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    return m.group(1) if m else ""


def read_records(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                x = json.loads(line)
                x["_line"] = n
                out.append(x)
    return out


def is_candidate_verdict(x):
    return "candidate" in x and "id" not in x


def apply_file(rows, cols, path, recs=None):
    """Apply one ledger file in place. Returns the list of (id, tier_before, tier_after)."""
    by = {r["id"]: r for r in rows}
    recs = read_records(path) if recs is None else recs
    step = os.path.splitext(os.path.basename(path))[0]
    date = file_date(path)
    moves, retier = [], set()
    for x in recs:
        if is_candidate_verdict(x) or "meta" in x:   # verdicts and the session's effort line change no row
            continue
        i = x["id"]
        if x.get("new"):
            if i in by:
                raise ValueError(f"{step}:{x['_line']}: {i} already exists")
            r = {c: "" for c in cols}
            r["id"] = i
            rows.append(r)
            by[i] = r
            before = "(new)"
            retier.add(i)
        else:
            if i not in by:
                raise ValueError(f"{step}:{x['_line']}: unknown id {i}")
            r = by[i]
            before = r["verify_tier"]
        s = x.get("set", {})
        if x.get("packet") == "m":            # a maintainer file may introduce a column
            for k in s:
                if k not in cols:
                    cols.append(k)
                    for rr in rows: rr.setdefault(k, "")
        bad = [k for k in s if k not in cols]
        if bad:
            raise ValueError(f"{step}:{x['_line']}: unknown columns {bad}")
        for k, v in s.items():
            r[k] = v
        who = f" by {x['by']}" if x.get("by") else ""
        r[NOTE] = f"{step}{who}: {x.get('note', '')}" + (f"; evidence {x['ev']}" if x.get("ev") else "")
        # a schema/metadata record is not a page verification: no verified_on / partB_* stamp
        if x.get("ev") and not x.get("blocked") and x.get("verifies", "schema_source" not in s):
            r["partB_pages_read"] = (r["partB_pages_read"] + "; " if r["partB_pages_read"] else "") + x["ev"]
            r["partB_source"] = (r["partB_source"] + "; " if r["partB_source"] else "") + step
            r["verified_on"] = date
        if any(k.startswith("chk_") or k in ("url_health", "browser_tier", "tier_cap") for k in s):
            retier.add(i)
        moves.append([i, before])
    for r in rows:
        if r["id"] in retier:
            summarise(r)
            r["verify_tier"] = tier_of(r)
            if r["verify_tier"] in ("Gold", "Silver") and not r.get("verification_level", "").startswith("file"):
                r["verification_level"] = "page-verified"
            r["tier"] = r["verify_tier"]
    return [(i, b, by[i]["verify_tier"]) for i, b in moves]


def replay(upto=None, extra=None):
    """Base + every ledger file (optionally stopping before `upto`, optionally adding `extra` files at the end).
    Returns rows, cols, applied file list, candidate verdicts."""
    rows, cols = read_csv(BASE)
    files = [f for f in ledger_files() if upto is None or os.path.basename(f) < os.path.basename(upto)]
    for f in (extra or []):
        if f not in files:
            files.append(f)
    verdicts = []
    for f in files:
        recs = read_records(f)
        for x in recs:
            for k in x.get("set", {}):
                if k not in cols:      # a ledger file may introduce a new column (maintainer files only; validate checks)
                    cols.append(k)
                    for r in rows: r.setdefault(k, "")
        apply_file(rows, cols, f, recs)
        verdicts += [dict(x, _file=os.path.basename(f)) for x in recs if is_candidate_verdict(x)]
    return rows, cols, files, verdicts


def counts(rows):
    k = [r for r in rows if r.get("round") != "2-pilot"]
    c = Counter(r["verify_tier"] for r in k)
    return {t: c.get(t, 0) for t in TIERS}


# ---- matching (never exact-DOI only) ----
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s;,\"'<>]+")


def norm_doi(s):
    m = DOI_RE.search((s or "").lower())
    if not m:
        return ""
    return re.sub(r"(\.v\d+|/v\d+|v\d+-\d+|\.\d{1,2})$", "", m.group(0).rstrip("."))


def all_dois(s):
    return {norm_doi(m) for m in DOI_RE.findall((s or "").lower())}


def norm_title(s):
    s = re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())
    return " ".join(w for w in s.split() if w not in {"the", "of", "and", "a", "an", "for", "in", "data", "dataset"})
