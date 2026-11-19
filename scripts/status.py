#!/usr/bin/env python3
"""Where am I? Shows the state of your own inventory work and changes nothing (run from the repo root).

    python scripts/status.py

Reports: work saved on this computer that was never submitted; your open reservations (claims) and how much of each is
done; your pull requests still being checked; and whether your copy is behind GitHub. Uses no Claude tokens.
"""
import glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

ITEM = re.compile(r"^- `([a-z-]+)` `(.+?)`", re.M)


def run(*a):
    try:
        p = subprocess.run(a, cwd=inv.ROOT, capture_output=True, text=True, timeout=40)
        return p.returncode, p.stdout.strip()
    except Exception:  # noqa: BLE001
        return 1, ""


def recs(path):
    try:
        return inv.read_records(path)
    except Exception:  # noqa: BLE001
        return []


todo = []
rc, branch = run("git", "branch", "--show-current")
print(f"Folder: {inv.ROOT}\nBranch: {branch or '?'}" + ("" if branch == "main" else "   (not main: a submission may have been interrupted)"))

# 1. work on disk that git has not committed
rc, st = run("git", "status", "--porcelain", "--", "ledger")
local = [l[3:].strip().strip('"') for l in st.splitlines() if l.strip()]
files = [f for f in local if f.endswith(".jsonl")]
done_local = set()
print("\nSaved on this computer, not submitted:")
if not local:
    print("  nothing")
for f in files:
    R = recs(os.path.join(inv.ROOT, f))
    meta = next((x["meta"] for x in R if "meta" in x), {})
    items = [x for x in R if "meta" not in x]
    done_local |= {x.get("id") or x.get("candidate") for x in items}
    print(f"  {f}: {len(items)} item(s) finished, kind '{meta.get('kind', '?')}'" + (f", for claim #{meta['claim']}" if meta.get("claim") else ""))
    todo.append(f"submit, continue or discard {f}: type /inventory in Claude Code and it will ask")
for f in [f for f in local if not f.endswith(".jsonl")]:
    print(f"  {f}")

# 2. GitHub: my claims and pull requests
rc, me = run("gh", "api", "user", "--jq", ".login")
if rc:
    print("\nGitHub: could not check (the GitHub CLI is missing or signed out; run python scripts/preflight.py)")
else:
    q = {}
    qp = os.path.join(inv.BUILD, "queue.csv")
    if os.path.exists(qp):
        q = {(r["kind"], r["item"]) for r in inv.read_csv(qp)[0]}
    rc, out = run("gh", "issue", "list", "--label", "claim", "--assignee", "@me", "--state", "open", "--json", "number,title,body,createdAt")
    claims = json.loads(out or "[]")
    print(f"\nYour open reservations ({me}):")
    if not claims:
        print("  none")
    for c in claims:
        its = ITEM.findall(c["body"] or "")
        saved = sum(1 for k, i in its if i in done_local)
        gone = sum(1 for x in its if x not in q)
        left = len(its) - max(saved, gone) if its else None
        print(f"  #{c['number']} {c['title']}  (opened {c['createdAt'][:10]})" + (f": {len(its)} items, {saved} saved here, {gone} already settled on GitHub, about {left} left" if its else ""))
        if not files:
            todo.append(f"claim #{c['number']} has nothing saved here: continue it (/inventory {c['number']}) or release it (gh issue close {c['number']})")
    rc, out = run("gh", "pr", "list", "--author", "@me", "--state", "open", "--json", "number,title,headRefName,statusCheckRollup")
    prs = json.loads(out or "[]")
    print("\nYour pull requests still open:")
    if not prs:
        print("  none")
    for p in prs:
        states = {(x.get("conclusion") or x.get("status") or "").upper() for x in (p.get("statusCheckRollup") or [])}
        s = "check FAILED" if "FAILURE" in states else "checks running" if states & {"IN_PROGRESS", "QUEUED", "PENDING"} else "checks passed, waiting (changes outside ledger/ need a maintainer)" if states else "no checks yet"
        print(f"  #{p['number']} {p['title']}: {s}")
        if "FAILURE" in states:
            todo.append(f"pull request #{p['number']} failed its check: tell Claude \"the check failed on my pull request\"")

# 3. behind GitHub?
run("git", "fetch", "--quiet", "origin")
rc, behind = run("git", "rev-list", "--count", "HEAD..origin/main")
if behind and behind != "0":
    print(f"\nYour copy is {behind} change(s) behind GitHub (Claude updates it at the start of /inventory).")

print("\nNothing needs doing." if not todo else "\nTo decide:\n" + "\n".join(f"  - {t}" for t in todo))
