#!/usr/bin/env python3
"""Build every derived file from base/ + ledger/ (run from the repo root; CI runs it on every push to main).

    python scripts/build.py            # writes build/ and the README state block
    python scripts/build.py --check    # builds in memory and fails if build/ is out of date (used on PRs)

Outputs (all generated; never edit by hand):
  build/inventory-all.csv          every dataset, every check, detail and evidence
  build/inventory-verified.csv     Gold + Silver, in the readable staging-list columns
  build/queues/*.csv               work for contributors, in stable batches (build/batches.json)
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

# ---- queues, in stable batches ----
CORE = ("chk_license", "chk_unit", "chk_temporal", "chk_access", "chk_join_key", "chk_format_gaia")
SET = ("pass", "warn", "fail", "n.a.")
live = [r for r in rows if r.get("round") != "2-pilot"]
Q = {  # queue: (prefix, batch size, packet, rows in order)
    "bronze-reads": ("BR", 10, "b", [r for r in live if r["verify_tier"] == "Bronze" and r.get("url_health") != "blocked"]),
    "silver-open": ("SO", 10, "b", [r for r in live if r["verify_tier"] == "Silver"
                                    and sum(r[c] in ("pass", "warn", "fail") for c in ("chk_license", "chk_unit", "chk_temporal", "chk_access")) <= 2]),
    "failed-successors": ("FS", 10, "b", [r for r in live if r["verify_tier"] == "Failed" and r.get("successor_verdict") in ("", "unresolved")]),
    "recipe-ready": ("RR", 5, "c", sorted([r for r in live if r["verify_tier"] in ("Gold", "Silver") and not r.get("verification_level", "").startswith("file")
                                           and not r.get("schema_source") and all(r[c] == "pass" for c in ("chk_license", "chk_access", "chk_join_key", "chk_format_gaia"))],
                                          key=lambda r: (r.get("wg_request") == "", r["verify_tier"] != "Gold", r["id"]))),
    "browser-needed": ("BN", 10, "d", [r for r in live if r["verify_tier"] == "Browser needed" or (r["verify_tier"] == "Bronze" and r.get("url_health") == "blocked")]),
}
# candidate families (packet e): drop families already in the inventory (any DOI in any field) or ruled out in the ledger
fam = list(csv.DictReader(open(os.path.join(inv.ROOT, "base", "candidate-families.csv"), encoding="utf-8-sig")))
inv_dois = set()
for r in rows:
    inv_dois |= inv.all_dois(" ".join(r.get(k, "") for k in ("persistent_id", "site_url", "access_url", "evidence_url", "notes", "partB_pages_read", "schema_source")))
ruled = {inv.norm_doi(v["candidate"]): v for v in verdicts}
fam_open = [f for f in fam if not (inv.all_dois(f["all_dois"] or f["doi"]) & (inv_dois | set(ruled)))]
fam_open.sort(key=lambda f: int(f["rank"] or 9999))

bpath = os.path.join(inv.ROOT, "build", "batches.json")
B = json.load(open(bpath, encoding="utf-8")) if os.path.exists(bpath) else {"next": {}, "batches": {}}
claimed = {}   # batch id -> first ledger file that names it
for f in files:
    for x in inv.read_records(f):
        if x.get("batch"):
            claimed.setdefault(x["batch"], os.path.basename(f))
qual = {q: [r["id"] for r in rs] for q, (_, _, _, rs) in Q.items()}
qual["candidates"] = [inv.norm_doi(f["doi"]) for f in fam_open]
size = {q: v[1] for q, v in Q.items()}
size["candidates"] = 10
prefix = {q: v[0] for q, v in Q.items()}
prefix["candidates"] = "CA"
for bid, b in B["batches"].items():
    if b["status"] != "open":
        continue
    if bid in claimed:
        b.update(status="done", done_in=claimed[bid])
        continue
    b["ids"] = [i for i in b["ids"] if i in set(qual.get(b["queue"], []))]
    if not b["ids"]:
        b.update(status="done", done_in="settled elsewhere")
for q, ids in qual.items():   # a row can sit in two queues (e.g. silver-open and recipe-ready): batches are per queue
    in_open = {i for b in B["batches"].values() if b["status"] == "open" and b["queue"] == q for i in b["ids"]}
    pool = [i for i in ids if i not in in_open]
    for k in range(0, len(pool), size[q]):
        n = B["next"].get(prefix[q], 1)
        B["next"][prefix[q]] = n + 1
        B["batches"][f"{prefix[q]}-{n:02d}"] = {"queue": q, "ids": pool[k:k + size[q]], "status": "open"}
put("build/batches.json", json.dumps(B, indent=1, sort_keys=True) + "\n")

hint = lambda r: " ".join((r.get("browser_pass_note") or r.get(inv.NOTE) or r.get("notes") or "").split())[:200]
openc = lambda r: ";".join(c[4:] for c in CORE if r.get(c, "") not in SET)
batch_of = {(b["queue"], i): bid for bid, b in B["batches"].items() if b["status"] == "open" for i in b["ids"]}
for q, (_, _, pk, rs) in Q.items():
    out = [{"batch": batch_of.get((q, r["id"]), ""), "packet": pk, "id": r["id"], "verify_tier": r["verify_tier"], "dataset_name": r["dataset_name"],
            "organization": r["organization"], "site_url": r["site_url"], "open_checks": openc(r), "hint": hint(r)} for r in rs]
    put(f"build/queues/{q}.csv", csv_text(sorted(out, key=lambda x: (x["batch"], x["id"])), list(out[0].keys()) if out else ["batch", "id"]))
fd = {inv.norm_doi(f["doi"]): f for f in fam_open}
cand = [{"batch": batch_of.get(("candidates", d), ""), "packet": "e", "doi": f["doi"], "title": f["title"], "publisher": f["publisher"], "year": f["year"],
         "anchors": f["anchors"], "region": f["region"], "siblings": f["n"], "all_dois": f["all_dois"]} for d, f in fd.items()]
put("build/queues/candidates.csv", csv_text(sorted(cand, key=lambda x: (x["batch"], x["doi"])), list(cand[0].keys()) if cand else ["batch", "doi"]))
rej = [{"doi": v["candidate"], "verdict": v.get("verdict", ""), "reason": v.get("reason", ""), "by": v.get("by", ""), "file": v["_file"]} for v in verdicts]
put("build/candidates-rejected.csv", csv_text(rej, ["doi", "verdict", "reason", "by", "file"]))

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

# ---- state ----
c = inv.counts(rows)
ob = Counter(b["queue"] for b in B["batches"].values() if b["status"] == "open")
contributors = sorted({x.get("by") for f in files for x in inv.read_records(f) if x.get("by")})
state = {"asof": asof, "rows": len(rows), "tiers": c, "verified": c["Gold"] + c["Silver"],
         "file_verified": sum(1 for r in rows if r.get("verification_level", "").startswith("file-verified")),
         "with_schema": sum(1 for r in rows if r.get("schema_source")), "with_key_vintage": sum(1 for r in rows if r.get("place_key_vintage")),
         "ledger_files": len(files), "contributors": contributors, "open_batches": dict(sorted(ob.items())),
         "candidate_families_open": len(fam_open), "candidates_ruled_out": len(rej)}
put("build/STATE.json", json.dumps(state, indent=1) + "\n")
block = (f"**As of {asof}:** {state['rows']} datasets assessed, **{state['verified']} verified** (Gold {c['Gold']}, Silver {c['Silver']}), "
         f"Bronze {c['Bronze']}, Browser needed {c['Browser needed']}, Failed {c['Failed']}. {state['file_verified']} file-verified; "
         f"{state['with_schema']} with a schema record; {state['with_key_vintage']} state their place-key vintage.\n\n"
         f"**Open work:** " + ", ".join(f"{n} {q} batch{'es' if n != 1 else ''}" for q, n in state["open_batches"].items())
         + f"; {state['candidate_families_open']} candidate families not yet checked. "
         f"**Ledger:** {len(files)} contribution file{'s' if len(files) != 1 else ''}"
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
print(f"{len(rows)} rows, {len(files)} ledger files; tiers {c}; open batches {dict(ob)}; candidate families {len(fam_open)}")
if CHECK and stale:
    print("out of date:", ", ".join(stale))
    sys.exit(1)
print("changed:", ", ".join(stale) if stale else "nothing")
