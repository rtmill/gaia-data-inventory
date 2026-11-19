#!/usr/bin/env python3
"""Build every derived file from base/ + ledger/ (run from the repo root; CI runs it on every push to main).

    python scripts/build.py            # writes build/ and the README state block
    python scripts/build.py --check    # builds in memory and fails if build/ is out of date (used on PRs)

Outputs (all generated; never edit by hand):
  build/inventory-all.csv          every dataset, every check, detail and evidence
  build/inventory-verified.csv     Gold + Silver, in the readable staging-list columns
  build/queue.csv                  every open item of work, one line each (slice and carve it with scripts/queue.py)
  build/effort.csv                 what contributors' sessions took (feeds the estimates)
  build/candidates-rejected.csv    candidate families ruled out by contributors (so they don't come back)
  build/site/inventory.json        data for the Data Inventory page on the OHDSI GIS site
  build/site/inventory-history.json
  build/STATE.json                 counts and dates; also rendered into README.md between the state markers
"""
import csv, io, json, os, re, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

CHECK = "--check" in sys.argv
OUT = {}   # path -> text (written at the end, or compared in --check)


def put(rel, text):
    OUT[os.path.join(inv.ROOT, rel)] = text


def csv_text(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return b.getvalue()


rows, cols, files, verdicts = inv.replay()
by = {r["id"]: r for r in rows}
asof = inv.file_date(files[-1]) if files else json.load(open(os.path.join(inv.ROOT, "base", "BASE.json"), encoding="utf-8"))["asof"]
put("build/inventory-all.csv", csv_text(rows, cols))

# ---- verified list in readable columns (explicit mapping; the old name-copy left title/publisher/landing_url blank) ----
first = lambda r, *ks: next((r.get(k, "") for k in ks if r.get(k, "")), "")
host = lambda u: re.sub(r"^https?://([^/]+).*$", r"\1", u or "")
VER = [("id", lambda r: r["id"]), ("tier", lambda r: r["verify_tier"]), ("title", lambda r: r["dataset_name"]),
       ("publisher", lambda r: r["organization"]), ("domain", lambda r: host(r.get("site_url"))), ("landing_url", lambda r: r.get("site_url", "")),
       ("access", lambda r: first(r, "access_confirmed", "access_type")), ("geography", lambda r: first(r, "finest_unit_confirmed", "finest_unit")),
       ("place_key", lambda r: first(r, "join_key_confirmed", "place_key_found", "place_key_type")),
       ("place_key_system", lambda r: r.get("place_key_system", "")), ("place_key_vintage", lambda r: r.get("place_key_vintage", "")),
       ("coverage", lambda r: first(r, "coverage_confirmed", "coverage")), ("temporal", lambda r: first(r, "temporal_confirmed", "temporal")),
       ("format", lambda r: first(r, "formats_confirmed", "format")), ("license", lambda r: first(r, "license_confirmed", "license")),
       ("license_class", lambda r: r.get("license_class", "")), ("update_cadence", lambda r: first(r, "update_cadence_confirmed", "update_cadence")),
       ("geometry_source", lambda r: r.get("geometry_source", "")), ("geometry_dependency", lambda r: r.get("geometry_dependency", "")),
       ("verification_level", lambda r: r.get("verification_level", "")), ("in_gaia", lambda r: r.get("in_gaia", "")),
       ("category", lambda r: first(r, "categories", "category")), ("region", lambda r: r.get("region", "")),
       ("last_checked", lambda r: first(r, "verified_on", "last_checked")),
       ("evidence", lambda r: first(r, "chk_license_evidence", "chk_unit_evidence", "chk_temporal_evidence", "evidence_url").split(";")[0].strip()),
       ("schema_source", lambda r: r.get("schema_source", ""))]
ver = [{k: f(r) for k, f in VER} for r in rows if r["verify_tier"] in ("Gold", "Silver") and r.get("round") != "2-pilot"]
put("build/inventory-verified.csv", csv_text(ver, [k for k, _ in VER]))

# ---- site data (same shape the GIS page's inventory.js reads) ----
CH = ["chk_link_live", "chk_license", "chk_temporal", "chk_recency", "chk_unit", "chk_access", "chk_join_key", "chk_format_gaia"]


def reg(r):
    p = r["id"].split("_")[0]
    m = {"us": "United States", "global": "Global", "eu": "Europe", "gb": "United Kingdom", "ca": "Canada", "au": "Australia", "nz": "Oceania", "hdx": "HDX (humanitarian)"}
    if p in m: return m[p]
    A = set("ke ng gh tz za et ug ma sn zm sl rw mw mz cd cm bf ml ne td so ss sd eg tn dz zw bw na".split())
    S = set("in bd pk ph id vn th kh la mm np lk cn jp kr tr sa ir iq af my tw".split())
    L = set("br mx co cl pe ar ec bo uy py ve gt hn sv ni cr pa cu do ht jm".split())
    E = set("fr de es it nl be pt ie at se no fi dk pl cz sk hu ro bg gr hr si ee lv lt lu mt cy ch is".split())
    return "Africa" if p in A else "Asia" if p in S else "Latin America" if p in L else "Europe" if p in E else "Other"


J = [{"id": r["id"], "n": r["dataset_name"], "o": r["organization"], "th": [c.strip() for c in (r.get("categories") or r.get("category") or "Other").split(";") if c.strip()], "rg": reg(r),
      "u": (r.get("finest_unit_confirmed") or r.get("finest_unit") or "").split("(")[0].strip()[:40],
      "t": r["verify_tier"], "lv": r.get("verification_level") or "not verified", "lc": r.get("license_class") or "unknown",
      "y": (r.get("temporal_confirmed") or r.get("temporal") or "")[:80], "ly": r.get("latest_year_final") or r.get("latest_year_confirmed") or r.get("latest_year", ""),
      "gs": r.get("geometry_source") or "unknown", "gd": r.get("geometry_dependency", ""), "pk": r.get("place_key_type", ""), "wg": r.get("wg_request", ""),
      "url": r.get("site_url") or r.get("access_url", ""), "ev": (r.get("chk_license_evidence") or r.get("chk_temporal_evidence") or r.get("evidence_url") or "").split(";")[0].strip(),
      "c": "".join({"pass": "p", "warn": "w", "fail": "f"}.get(r.get(c, ""), "-") for c in CH), "bl": r.get("verify_blockers", "")[:160],
      "fv": r.get("file_status", ""), "fk": r.get("place_key_found", "")[:120], "fg": r.get("geometry_found", "")[:80], "fy": r.get("years_found", "")[:60],
      "fm": r.get("file_mismatches", "")[:200], "vo": r.get("verified_on", ""), "gc": (r.get("in_gaia") or "").strip()} for r in rows]
put("build/site/inventory.json", json.dumps({"asof": asof, "checks": ["link", "licence", "years", "recency", "unit", "access", "join key", "format"], "rows": J}, ensure_ascii=False))
H = json.load(open(os.path.join(inv.ROOT, "base", "history.json"), encoding="utf-8"))
snaps, codes = list(H["snaps"]), dict(H["t"])
if files:   # one point for the ledger era as it stands now
    T = {"Gold": "G", "Silver": "S", "Bronze": "B", "Browser needed": "N", "Failed": "F"}
    snaps.append({"d": asof, "it": f"ledger ({len(files)})", "l": f"Ledger: {len(files)} contribution files since the base", "n": len(rows)})
    for r in rows:
        codes[r["id"]] = codes.get(r["id"], "-" * len(H["snaps"])) + T.get(r["verify_tier"], "-")
cur = {r["id"] for r in rows}
put("build/site/inventory-history.json", json.dumps({"cat": H["cat"], "iterations": H["iterations"], "since": H["since"], "snaps": snaps,
                                                    "t": {i: v for i, v in sorted(codes.items()) if i in cur}}, ensure_ascii=False, separators=(",", ":")))

# ---- the queue: every open item, one line each (scripts/queue.py slices it and carves claims from it) ----
CORE = ("chk_license", "chk_unit", "chk_temporal", "chk_access", "chk_join_key", "chk_format_gaia")
SET = ("pass", "warn", "fail", "n.a.")
live = [r for r in rows if r.get("round") != "2-pilot"]
touched = Counter(x["id"] for f in files for x in inv.read_records(f) if x.get("id"))
KINDS = {  # kind: (packet, rows)
    "read": ("b", [r for r in live if r["verify_tier"] == "Bronze" and r.get("url_health") != "blocked"]),
    "settle": ("b", [r for r in live if r["verify_tier"] == "Silver"
                     and sum(r[c] in ("pass", "warn", "fail") for c in ("chk_license", "chk_unit", "chk_temporal", "chk_access")) <= 2]),
    "successor": ("b", [r for r in live if r["verify_tier"] == "Failed" and r.get("successor_verdict") in ("", "unresolved")]),
    "schema": ("c", [r for r in live if r["verify_tier"] in ("Gold", "Silver") and not r.get("verification_level", "").startswith("file")
                     and not r.get("schema_source") and all(r[c] == "pass" for c in ("chk_license", "chk_access", "chk_join_key", "chk_format_gaia"))]),
    "person-read": ("d", [r for r in live if r["verify_tier"] == "Browser needed" or (r["verify_tier"] == "Bronze" and r.get("url_health") == "blocked")]),
}
hint = lambda r: " ".join((r.get("browser_pass_note") or r.get(inv.NOTE) or r.get("notes") or "").split())[:200]
QC = ["kind", "item", "packet", "tier", "title", "publisher", "host", "region", "category", "wg_request", "open_checks", "touched", "hint"]
queue = []
for kind, (pk, rs) in KINDS.items():
    for r in rs:
        queue.append({"kind": kind, "item": r["id"], "packet": pk, "tier": r["verify_tier"], "title": r["dataset_name"], "publisher": r["organization"],
                      "host": host(r.get("site_url")), "region": reg(r), "category": (r.get("categories") or r.get("category") or "Other").split(";")[0].strip(),
                      "wg_request": r.get("wg_request", ""), "open_checks": ";".join(c[4:] for c in CORE if r.get(c, "") not in SET),
                      "touched": str(touched.get(r["id"], 0)), "hint": hint(r)})
# candidate families: drop those already in the inventory (any DOI in any field) or ruled out in the ledger
fam = list(csv.DictReader(open(os.path.join(inv.ROOT, "base", "candidate-families.csv"), encoding="utf-8-sig")))
import glob
for lp in sorted(glob.glob(os.path.join(inv.LEDGER, "leads", "*.csv"))):   # leads contributors found by continuing an approach
    for n, l in enumerate(csv.DictReader(open(lp, encoding="utf-8-sig"))):
        if l.get("ref"):
            fam.append({"doi": l["ref"].strip(), "all_dois": l["ref"].strip(), "title": l.get("title", ""), "publisher": l.get("publisher", ""), "year": l.get("year", ""),
                        "anchors": l.get("anchor", ""), "region": l.get("region", ""), "n": "1", "rank": str(100000 + n), "source": os.path.basename(lp)})
key = lambda ref: inv.norm_doi(ref) or ref.strip().lower().rstrip("/")
known_urls = {u.strip().lower().rstrip("/") for r in rows for u in (r.get("site_url", ""), r.get("access_url", "")) if u.strip()}
inv_dois = set()
for r in rows:
    inv_dois |= inv.all_dois(" ".join(r.get(k, "") for k in ("persistent_id", "site_url", "access_url", "evidence_url", "notes", "partB_pages_read", "schema_source")))
ruled = {key(v["candidate"]) for v in verdicts}
seen_ref = set()
fam_open = []
for f in fam:
    k = key(f["doi"])
    if k in seen_ref or k in ruled or k in known_urls or (inv.all_dois(f["all_dois"] or f["doi"]) & (inv_dois | ruled)):
        continue
    seen_ref.add(k)
    fam_open.append(f)
for f in sorted(fam_open, key=lambda f: int(f["rank"] or 9999)):
    queue.append({"kind": "candidate", "item": f["doi"], "packet": "e", "tier": "", "title": f["title"], "publisher": f["publisher"],
                  "host": f["doi"].split("/")[0], "region": f["region"], "category": f["anchors"].split(";")[0], "wg_request": "",
                  "open_checks": "", "touched": "0", "hint": (f"lead from {f['source']}" if f.get("source") else f"{f['n']} DOI(s) in the family; {f['year']}")})
put("build/queue.csv", csv_text(queue, QC))
rej = [{"doi": v["candidate"], "verdict": v.get("verdict", ""), "reason": v.get("reason", ""), "by": v.get("by", ""), "file": v["_file"]} for v in verdicts]
put("build/candidates-rejected.csv", csv_text(rej, ["doi", "verdict", "reason", "by", "file"]))
# effort actually spent, from the "meta" line contributors' sessions add to their ledger files
eff = [dict(x["meta"], file=os.path.basename(f)) for f in files for x in inv.read_records(f) if "meta" in x]
put("build/effort.csv", csv_text(eff, ["file", "by", "kind", "items", "minutes", "fetches", "tokens"]))

# ---- state ----
c = inv.counts(rows)
ob = Counter(q["kind"] for q in queue)
contributors = sorted({x.get("by") for f in files for x in inv.read_records(f) if x.get("by")})
state = {"asof": asof, "rows": len(rows), "tiers": c, "verified": c["Gold"] + c["Silver"],
         "file_verified": sum(1 for r in rows if r.get("verification_level", "").startswith("file-verified")),
         "with_schema": sum(1 for r in rows if r.get("schema_source")), "with_key_vintage": sum(1 for r in rows if r.get("place_key_vintage")),
         "ledger_files": len(files), "contributors": contributors, "queue": dict(sorted(ob.items())), "candidates_ruled_out": len(rej)}
spec = sum(1 for r in live if r["verify_tier"] in ("Gold", "Silver") and r.get("place_key_system") and r.get("columns_found") and (r.get("geometry_found") or r.get("geometry_source")))
state["funnel"] = {"leads": ob["candidate"], "listed_unverified": c["Bronze"] + c["Browser needed"] + c["Failed"], "verified": c["Gold"] + c["Silver"],
                   "verified_thin": ob["settle"], "specified": spec}
put("build/STATE.json", json.dumps(state, indent=1) + "\n")
block = (f"**As of {asof}:** {state['rows']} datasets assessed, **{state['verified']} verified** (Gold {c['Gold']}, Silver {c['Silver']}), "
         f"Bronze {c['Bronze']}, Browser needed {c['Browser needed']}, Failed {c['Failed']}. {state['file_verified']} file-verified; "
         f"{state['with_schema']} with a schema record; {state['with_key_vintage']} state their place-key vintage.\n\n"
         f"**Where things stand:** {state['funnel']['leads']} leads not yet looked at → {state['funnel']['listed_unverified']} listed but unverified → "
         f"{state['verified']} verified ({state['funnel']['verified_thin']} of them on thin evidence) → {spec} fully specified (columns, place key and vintage, geometry: what a recipe needs). "
         f"Open work: {len(queue)} items; see it with `python scripts/queue.py`. **Ledger:** {len(files)} contribution file{'s' if len(files) != 1 else ''}"
         + (f" from {len(contributors)} contributor{'s' if len(contributors) != 1 else ''}." if contributors else "."))
rp = os.path.join(inv.ROOT, "README.md")
readme = open(rp, encoding="utf-8").read()
readme = re.sub(r"(<!-- state:start -->\n).*?(\n<!-- state:end -->)", lambda m: m.group(1) + block + m.group(2), readme, flags=re.S)
put("README.md", readme)

# ---- write or check ----
stale = []
for p, text in OUT.items():
    old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    if old != text:
        stale.append(os.path.relpath(p, inv.ROOT))
        if not CHECK:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8", newline="").write(text)
print(f"{len(rows)} rows, {len(files)} ledger files; tiers {c}; queue {dict(ob)}")
if CHECK and stale:
    print("out of date:", ", ".join(stale))
    sys.exit(1)
print("changed:", ", ".join(stale) if stale else "nothing")
