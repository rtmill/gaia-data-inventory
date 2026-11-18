#!/usr/bin/env python3
"""Tidy claim issues after a build (run by CI on main; needs the gh CLI and GH_TOKEN).

Work is claimed from the queue with scripts/queue.py --claim, which opens one issue per claim. This script:
  - closes the pre-cut "[batch ...]" issues from the first day (the queue replaced them);
  - closes a claim whose items have all left the queue (settled by a merged contribution);
  - comments once on a claim with no activity for 14 days, so its items can be released by closing it.
"""
import csv, datetime, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

DRY = "--dry-run" in sys.argv
ITEM = re.compile(r"^- `([a-z-]+)` `(.+?)`", re.M)


def gh(*a):
    if DRY and a[0] == "issue" and a[1] in ("close", "comment"):
        print("DRY:", " ".join(a)[:150])
        return ""
    return subprocess.run(["gh", *a], capture_output=True, text=True, check=True).stdout


q = {(r["kind"], r["item"]) for r in csv.DictReader(open(os.path.join(inv.BUILD, "queue.csv"), encoding="utf-8"))}
for i in json.loads(gh("issue", "list", "--label", "batch", "--state", "open", "--limit", "200", "--json", "number")):
    gh("issue", "close", str(i["number"]), "--comment", "Pre-cut batches are replaced by the queue: carve what you want with `python scripts/queue.py` (see CONTRIBUTING.md).")
now = datetime.datetime.now(datetime.timezone.utc)
for i in json.loads(gh("issue", "list", "--label", "claim", "--state", "open", "--limit", "500", "--json", "number,body,updatedAt,comments")):
    items = ITEM.findall(i["body"] or "")
    if items and not any(x in q for x in items):
        gh("issue", "close", str(i["number"]), "--comment", "All items settled.")
    elif (now - datetime.datetime.fromisoformat(i["updatedAt"].replace("Z", "+00:00"))).days >= 14 \
            and not any("still working on this" in (c.get("body") or "") for c in i["comments"][-1:]):
        gh("issue", "comment", str(i["number"]), "--body", "No activity for two weeks. Are you still working on this? Close the issue to release its items back to the queue.")
print("claims tidied")
