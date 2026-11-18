#!/usr/bin/env python3
"""Keep one GitHub issue per open batch (run by CI after build.py on main; needs the gh CLI and GH_TOKEN).

    python scripts/sync_issues.py [--dry-run] [--max-new N]

Opens an issue "[batch XX-nn] <queue>: n items" for each open batch that has none (at most N new per run, default 20,
so the issue list stays readable), and closes the issue of each batch that is done, with a note saying where.
Assigning yourself the issue is the claim.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

DRY = "--dry-run" in sys.argv
MAXN = int(sys.argv[sys.argv.index("--max-new") + 1]) if "--max-new" in sys.argv else 20
LABEL = "batch"
TITLE = re.compile(r"^\[batch ([A-Z]{2}-\d+)\]")
WHAT = {"bronze-reads": ("b", "Read these Bronze rows' publisher pages and settle their open checks."),
        "silver-open": ("b", "These Silver rows have two or fewer of licence, unit, years and access settled; settle them."),
        "failed-successors": ("b", "These rows failed (dead or moved); find a successor page or confirm they are retired."),
        "recipe-ready": ("c", "Verified rows with no schema yet: read columns, place key (system, level, vintage) and geometry from metadata."),
        "browser-needed": ("d", "These pages block scripts. Open them in your own browser and record what they say (no AI needed)."),
        "candidates": ("e", "Candidate families from DataCite: check each, add the real datasets as rows, rule out the rest.")}


def gh(*a, inp=None):
    if DRY and a[:2] in (("issue", "create"), ("issue", "close"), ("label", "create")):
        print("DRY:", " ".join(a)[:160])
        return ""
    return subprocess.run(["gh", *a], input=inp, capture_output=True, text=True, check=True).stdout


B = json.load(open(os.path.join(inv.BUILD, "batches.json"), encoding="utf-8"))["batches"]
issues = json.loads(gh("issue", "list", "--label", LABEL, "--state", "all", "--limit", "1000", "--json", "number,title,state"))
have = {}
for i in issues:
    m = TITLE.match(i["title"])
    if m:
        have[m.group(1)] = i
try:
    gh("label", "create", LABEL, "--color", "0e8a16", "--description", "A claimable batch of inventory work")
except subprocess.CalledProcessError:
    pass   # exists
new = 0
for bid, b in sorted(B.items(), key=lambda kv: (kv[0][:2], int(kv[0][3:]))):
    i = have.get(bid)
    if b["status"] == "open" and not i and new < MAXN:
        pk, what = WHAT[b["queue"]]
        body = (f"**Packet {pk}, queue `{b['queue']}`.** {what}\n\n"
                f"**To take it:** assign yourself this issue, then in a clone of this repo run `claude` and type `/inventory {bid}`. "
                f"See `CONTRIBUTING.md`.\n\n**Items:**\n" + "\n".join(f"- `{x}`" for x in b["ids"]) +
                f"\n\nYour pull request closes this issue with `Closes #<this number>`.")
        gh("issue", "create", "--title", f"[batch {bid}] {b['queue']}: {len(b['ids'])} items", "--label", LABEL, "--body-file", "-", inp=body)
        new += 1
    elif b["status"] == "done" and i and i["state"] == "OPEN":
        gh("issue", "close", str(i["number"]), "--comment", f"Done: {b.get('done_in', 'settled')}.")
print(f"opened {new}; batches {len(B)}; issues known {len(have)}")
