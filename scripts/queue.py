#!/usr/bin/env python3
"""The work queue: see it, slice it, estimate it, and carve off as much as you want (run from the repo root).

    python scripts/queue.py                                   overview: each kind of work, how much is open, what it costs
    python scripts/queue.py --by region [filters]             slice the open items by kind, region, category, host, tier or publisher
    python scripts/queue.py --kind candidate --region Africa --n 15     show the 15 items you'd get, with the estimate
    python scripts/queue.py ... --n 15 --claim                same, and claim them: opens a GitHub issue assigned to you
    python scripts/queue.py --issue 23                        the items of claim #23
    python scripts/queue.py --approaches                      every approach tried so far: result, cost, verdict, what is left

Filters: --kind, --region, --category, --host, --tier, --publisher (substring, case-insensitive), --match (in the title),
--wg (working-group request rows only), --fresh (never touched in the ledger). Items in someone's open claim are left out.
Estimates come from method/estimates.csv (measured on earlier runs) and, once there are sessions to learn from,
from build/effort.csv (what contributors' sessions here actually took).
"""
import argparse, csv, json, os, re, statistics, subprocess, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

load = lambda p: list(csv.DictReader(open(p, encoding="utf-8-sig", newline=""))) if os.path.exists(p) else []
ITEM = re.compile(r"^- `([a-z-]+)` `(.+?)`", re.M)
WHAT = {"read": "Bronze rows: read the publisher's page, settle the checks",
        "settle": "Silver rows with two or fewer of licence, unit, years, access settled",
        "successor": "Failed rows: find where the page moved, or confirm it is retired",
        "schema": "Verified rows: columns, place key and vintage from metadata records",
        "person-read": "Pages that block scripts: a person opens them (almost no tokens)",
        "candidate": "DataCite candidate families: add the real datasets, rule out the rest"}


def gh(*a, inp=None):
    return subprocess.run(["gh", *a], input=inp, capture_output=True, text=True, check=True).stdout


def claims():
    """(kind, item) -> issue number, for every open claim issue. Empty (with a note) if gh isn't available."""
    try:
        out = {}
        for i in json.loads(gh("issue", "list", "--label", "claim", "--state", "open", "--limit", "500", "--json", "number,body")):
            for k, it in ITEM.findall(i["body"] or ""):
                out[(k, it)] = i["number"]
        return out
    except Exception:  # noqa: BLE001
        print("(couldn't read open claims with gh: check the open 'claim' issues yourself before starting)")
        return {}


def estimates():
    est = {r["kind"]: r for r in load(os.path.join(inv.ROOT, "method", "estimates.csv"))}
    seen = {}
    for r in load(os.path.join(inv.BUILD, "effort.csv")):
        try:
            n = float(r["items"])
            seen.setdefault(r["kind"], []).append((float(r["minutes"]) / n if r["minutes"] else None, float(r["tokens"]) / n if r["tokens"] else None))
        except (ValueError, ZeroDivisionError):
            pass
    for k, v in seen.items():
        if len(v) >= 3 and k in est:   # enough sessions here: prefer what they actually took
            m = [a for a, _ in v if a is not None]
            t = [b for _, b in v if b is not None]
            if m: est[k]["minutes_per_item"] = f"{statistics.median(m):.1f}"
            if t: est[k]["tokens_per_item"] = f"{statistics.median(t):.0f}"
            est[k]["basis"] = f"median of {len(v)} sessions in this repo"
    return est


def cost(kind, n, est):
    e = est.get(kind, {})
    m, t = e.get("minutes_per_item"), e.get("tokens_per_item")
    g = e.get("tokens_guess")
    tok = f"about {float(t) * n / 1000:.0f}k tokens (measured)" if t else (f"roughly {float(g) * n / 1000:.0f}k tokens (a guess, not measured yet)" if g else "tokens not measured yet")
    return tok + (f", about {float(m) * n:.3g} min of Claude working" if m else "")


ap = argparse.ArgumentParser(add_help=False)
for f in ("kind", "region", "category", "host", "tier", "publisher", "match", "by", "approach"):
    ap.add_argument("--" + f)
ap.add_argument("--n", type=int); ap.add_argument("--issue", type=int)
for f in ("claim", "wg", "fresh", "help", "approaches"):
    ap.add_argument("--" + f, action="store_true")
a = ap.parse_args()
if a.help:
    sys.exit(__doc__)
if a.approaches or a.approach:
    AP = load(os.path.join(inv.ROOT, "method", "approaches.csv"))
    if a.approaches:      # short list of what can be continued now; --approach "<name>" for one in full, --approaches --all for every row
        for r in AP:
            if "--all" in sys.argv or r["continue_with"].startswith("brief:"):
                print(f"{r['approach']} | last time: {r['result'][:110]} | verdict: {r['verdict'][:70]} | left: {r['remaining'][:120]}")
        print('One in full: --approach "<name>". Every approach, including those done through the queue, closed, or needing a maintainer brief: --approaches --all')
        sys.exit()
    for r in [r for r in AP if a.approach.lower() in r["approach"].lower()]:
        print(f"{r['approach']}   [{r['moves']}]   tried in {r['tried_in']}\n  how:       {r['how']}\n  result:    {r['result']}\n  cost:      {r['cost']}\n"
              f"  verdict:   {r['verdict']}\n  left:      {r['remaining']}\n  next:      {r['next_step']}\n  continue:  {r['continue_with']}\n")
    sys.exit()
if a.issue:
    body = json.loads(gh("issue", "view", str(a.issue), "--json", "body,title,assignees"))
    q = {(r["kind"], r["item"]): r for r in load(os.path.join(inv.BUILD, "queue.csv"))}
    print(body["title"], "| assigned:", ", ".join(x["login"] for x in body["assignees"]) or "nobody")
    for k, it in ITEM.findall(body["body"] or ""):
        r = q.get((k, it))
        print(f"{k}  {it}  " + (f"{r['title'][:80]} | open: {r['open_checks']} | {r['hint'][:120]}" if r else "(no longer in the queue: already settled)"))
    sys.exit()

Q = load(os.path.join(inv.BUILD, "queue.csv"))
est = estimates()
taken = claims()
free = [r for r in Q if (r["kind"], r["item"]) not in taken]
sel = free
for f in ("kind", "region", "category", "host", "tier", "publisher"):
    v = getattr(a, f)
    if v:
        sel = [r for r in sel if v.lower() in r[f].lower()] if f in ("publisher", "host", "category", "region") else [r for r in sel if r[f].lower() == v.lower()]
if a.match: sel = [r for r in sel if a.match.lower() in r["title"].lower()]
if a.wg: sel = [r for r in sel if r["wg_request"]]
if a.fresh: sel = [r for r in sel if r["touched"] == "0"]
filtered = sel is not free or a.match or a.wg or a.fresh or any(getattr(a, f) for f in ("kind", "region", "category", "host", "tier", "publisher"))

if a.by:
    c = Counter(r[a.by] or "(none)" for r in sel)
    print(f"{len(sel)} open items" + (" matching your filters" if filtered else "") + f", by {a.by}:")
    for k, n in c.most_common(40):
        print(f"  {n:4d}  {k}")
elif a.n:
    kinds = {r["kind"] for r in sel}
    if len(kinds) != 1:
        sys.exit(f"pick one kind with --kind (your filters match: {', '.join(sorted(kinds)) or 'nothing'})")
    kind = kinds.pop()
    sel.sort(key=lambda r: (r["wg_request"] == "", int(r["touched"])))   # WG requests first, then never-touched; otherwise queue order
    take = sel[:a.n]
    print(f"{len(take)} of {len(sel)} matching '{kind}' items: {cost(kind, len(take), est)} ({est.get(kind, {}).get('basis', 'no estimate')})")
    for r in take:
        print(f"  {r['item']}  {r['title'][:80]} | {r['publisher'][:30]} | {r['region']} | {r['category']}" + (f" | open: {r['open_checks']}" if r["open_checks"] else ""))
    if a.claim and take:
        me = gh("api", "user", "--jq", ".login").strip()
        body = (f"**{kind}**: {WHAT[kind]}.\n\nEstimate: {cost(kind, len(take), est)}.\n\n" + "\n".join(f"- `{kind}` `{r['item']}` {r['title'][:90]}" for r in take)
                + "\n\nWork it with `/inventory <this issue number>`. The pull request closes this issue; anything left unfinished goes back to the queue.")
        try: gh("label", "create", "claim", "--color", "0e8a16", "--description", "Work someone has carved from the queue")
        except subprocess.CalledProcessError: pass
        print("claimed:", gh("issue", "create", "--title", f"[claim] {kind}: {len(take)} items ({me})", "--label", "claim", "--assignee", "@me", "--body-file", "-", inp=body).strip())
    elif take:
        print("Add --claim to take these (opens an issue assigned to you).")
else:
    c, f = Counter(r["kind"] for r in Q), Counter(r["kind"] for r in sel)
    st = json.load(open(os.path.join(inv.BUILD, "STATE.json"), encoding="utf-8")).get("funnel", {})
    print(f"Stages: {st.get('leads')} leads -> {st.get('listed_unverified')} listed, unverified -> {st.get('verified')} verified "
          f"({st.get('verified_thin')} on thin evidence) -> {st.get('specified')} fully specified (ready to write a recipe from)")
    print(f"{len(Q)} open items, {len(Q) - len(free)} in someone's claim" + (f"; {len(sel)} match your filters" if filtered else "") + "\n")
    nap = sum(1 for r in load(os.path.join(inv.ROOT, "method", "approaches.csv")) if r["continue_with"].startswith("brief:"))
    print(f"explore: {nap} approaches with work left, or design a new one   moves: nothing -> lead (and often on to listed)\n"
          f"  you do:    Continue a way of searching that was tried before, from where it stopped, or work out a new one with Claude\n"
          f"  produces:  New leads for the queue, some datasets listed along the way, and a note on how well the approach worked\n"
          f"  why:       The lead pool is finite ({c['candidate']} left); this is where new datasets come from once it is used up\n"
          f"  cost:      Open-ended: you set the budget and Claude sizes the run to it. Past runs added 20 to 26 datasets each\n"
          f"  list them: python scripts/queue.py --approaches")
    for k in [k for k in est if k in WHAT] + [k for k in WHAT if k not in est]:
        if c[k]:
            e = est.get(k, {})
            m, rate = e.get("minutes_per_item"), e.get("result_rate")
            half = (f"30 min is about {30 / float(m):.0f} items" + (f", giving about {30 / float(m) * float(rate):.0f} {e.get('result_label', 'results')}" if rate else "") + (f" ({e['rate_note']})" if e.get("rate_note") else "")) if m else ""
            print(f"{k}: {f[k]} free of {c[k]}   moves a dataset: {e.get('moves', '')}\n  you do:    {WHAT[k]}\n  produces:  {e.get('produces', '')}\n  why:       {e.get('why', '')}\n"
                  f"  cost:      {cost(k, 1, est)} per item. All {c[k]}: {cost(k, c[k], est)}. {half}\n  basis:     {e.get('basis', '')}"
                  + (f"\n  maintainers suggest this now: {e['suggest']}" if e.get("suggest") else ""))
    print("\nSlice: --by region|category|host|tier|publisher|kind (with any filters). Carve: --kind K [filters] --n N [--claim].")
