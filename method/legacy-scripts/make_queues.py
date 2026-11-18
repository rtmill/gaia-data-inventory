#!/usr/bin/env python3
"""Cut the contributor queues from the inventory master (run by build_publish_package.py, or by hand).

    python make_queues.py <inventory-all.csv> <queues_dir>

Each queue is a compact CSV in batches of 10: batch, id, verify_tier, dataset_name, organization, site_url,
open_checks, hint. Rows needing the working group (TODO tier 4) or a maintainer decision are not queued.
"""
import csv, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
CORE = ("chk_license", "chk_unit", "chk_temporal", "chk_access", "chk_join_key", "chk_format_gaia")
SET = ("pass", "warn", "fail", "n.a.")
rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig", newline="")))
openc = lambda r: ";".join(c[4:] for c in CORE if r.get(c, "") not in SET)
hint = lambda r: " ".join((r.get("browser_pass_note") or r.get("run_2026_11_02_note") or r.get("notes") or "").split())[:200]
gs = ("Gold", "Silver")
Q = {
    # b: Bronze rows a script can reach; settle the open checks from the publisher's pages
    ("bronze-reads", "BR"): [r for r in rows if r["verify_tier"] == "Bronze" and r.get("url_health") != "blocked"],
    # b: Silver rows with two or fewer of licence/unit/years/access settled (TODO 4.10)
    ("silver-open", "SO"): [r for r in rows if r["verify_tier"] == "Silver"
                            and sum(r[c] in ("pass", "warn", "fail") for c in ("chk_license", "chk_unit", "chk_temporal", "chk_access")) <= 2],
    # b: Failed rows whose successor is unresolved
    ("failed-successors", "FS"): [r for r in rows if r["verify_tier"] == "Failed" and r.get("successor_verdict") in ("", "unresolved")],
    # c: verified, page-only rows with licence, access, join key and format all pass; WG requests first
    ("recipe-ready", "RR"): sorted([r for r in rows if r["verify_tier"] in gs and not r.get("verification_level", "").startswith("file")
                                    and all(r[c] == "pass" for c in ("chk_license", "chk_access", "chk_join_key", "chk_format_gaia"))],
                                   key=lambda r: (r.get("wg_request") == "", r["verify_tier"] != "Gold", r["id"])),
    # d: blocked for scripts; a person opens these in their own browser
    ("browser-needed", "BN"): [r for r in rows if r["verify_tier"] == "Browser needed" or (r["verify_tier"] == "Bronze" and r.get("url_health") == "blocked")],
}
os.makedirs(OUT, exist_ok=True)
for (name, pre), rs in Q.items():
    rs = [r for r in rs if r.get("round") != "2-pilot"]   # pilot rows are capped at Bronze until a maintainer promotes them
    with open(os.path.join(OUT, name + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["batch", "id", "verify_tier", "dataset_name", "organization", "site_url", "open_checks", "hint"])
        for i, r in enumerate(rs):
            w.writerow([f"{pre}-{i // 10 + 1:02d}", r["id"], r["verify_tier"], r["dataset_name"], r["organization"], r["site_url"], openc(r), hint(r)])
    print(f"{name}: {len(rs)} rows, {(len(rs) + 9) // 10} batches")
