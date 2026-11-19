#!/usr/bin/env python3
"""Check ledger files before they are merged (run from the repo root; CI runs it on every pull request).

    python scripts/validate.py ledger/<file>.jsonl [more files]
    python scripts/validate.py --changed [--against origin/main]    # every ledger file this branch adds
    python scripts/validate.py --maintainer ...                       # also allows new columns (method changes)

Checks: record shape; ids exist (or are new and unused); columns exist and aren't computed; check values use the
vocabulary; every check set to pass/warn/fail has evidence; unit terms come from method/unit-vocabulary.csv;
packet c has its packet file; the files apply cleanly on top of the current ledger; and, with --against, that no
row you touch was changed on that branch since you branched (re-check those rows, then rebase).
Exit 1 on any error; warnings don't block.
"""
import difflib, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

args = sys.argv[1:]
MAINT = "--maintainer" in args
against = args[args.index("--against") + 1] if "--against" in args else None
paths = [a for a in args if a.endswith(".jsonl")]


def git(*a):
    return subprocess.run(["git", *a], cwd=inv.ROOT, capture_output=True, text=True, check=True).stdout


if "--changed" in args:
    ref = against or "origin/main"
    mb = git("merge-base", "HEAD", ref).strip()
    paths += [os.path.join(inv.ROOT, p) for p in git("diff", "--name-only", "--diff-filter=AM", mb, "HEAD", "--", "ledger/").split()
              if p.endswith(".jsonl")]
paths = sorted({os.path.abspath(p) for p in paths})
if not paths:
    print("no ledger files to check")
    sys.exit(0)

errs, warns = [], []
E = lambda f, n, m: errs.append(f"{f}:{n}: {m}")
W = lambda f, n, m: warns.append(f"{f}:{n}: {m}")

# state before these files
mine = {os.path.basename(p) for p in paths}
rows, cols = inv.read_csv(inv.BASE)
for f in inv.ledger_files():
    if os.path.basename(f) not in mine:
        try:
            inv.apply_file(rows, cols, f)
        except Exception as e:  # noqa: BLE001
            print(f"The repository's own ledger does not replay ({os.path.basename(f)}: {e}).\n"
                  "This is not a problem with your file. Nothing can be checked until a maintainer fixes it: please tell Robert (rtmill).")
            sys.exit(2)
IDS = {r["id"]: r for r in rows}
COLS = set(cols)
UNITS = {r["term"].strip() for r in inv.read_csv(os.path.join(inv.ROOT, "method", "unit-vocabulary.csv"))[0]}
LIC = {"open", "attribution", "non-commercial", "registration", "restricted", "unknown", "public_domain_us_federal"}
VOCAB = {"pass", "warn", "fail", "n.a.", "not_checked"}
URL = re.compile(r"^https?://\S+$")
PACKET_KEYS = ("schema_source", "columns", "place_key", "geometry", "evidence")
PROTECTED = inv.COMPUTED | {"round", "id"}
fams = {r["item"].lower() for r in inv.read_csv(os.path.join(inv.BUILD, "queue.csv"))[0] if r["kind"] == "candidate"}
urls_ok = lambda v: all(URL.match(u.strip()) for u in v.split(";") if u.strip())

touched = {}
for path in paths:
    fn = os.path.basename(path)
    if not re.match(r"^\d{4}-\d{2}-\d{2}-[A-Za-z0-9-]+-[a-z0-9.-]+\.jsonl$", fn):
        E(fn, 0, "name must be <YYYY-MM-DD>-<github-handle>-<slug>-<HHMM>.jsonl (lowercase slug)")
    elif not MAINT and not re.search(r"-\d{4}\.jsonl$", fn):
        E(fn, 0, "name must end with the time you started, -<HHMM>.jsonl (e.g. 2026-11-19-yourhandle-read-1432.jsonl), so two sessions never share a name")
    if os.path.dirname(path) != os.path.abspath(inv.LEDGER):
        E(fn, 0, "ledger files live directly in ledger/")
    try:
        recs = inv.read_records(path)
    except json.JSONDecodeError as e:
        E(fn, 0, f"not JSON lines: {e}")
        continue
    seen = set()
    for x in recs:
        n = x["_line"]
        if "meta" in x:                          # the session's effort line
            m = x["meta"]
            if not (isinstance(m, dict) and m.get("by") and m.get("kind") and isinstance(m.get("items"), int)):
                E(fn, n, "meta needs by, kind and items (a number); minutes, fetches, tokens are optional")
            continue
        for k in ("by", "packet", "note"):
            if not x.get(k):
                E(fn, n, f"missing '{k}'")
        if x.get("packet") not in ("a", "b", "c", "d", "e", "m"):
            E(fn, n, "packet must be a, b, c, d or e (m = maintainer)")
        if x.get("packet") == "m" and not MAINT:
            E(fn, n, "packet m is for maintainer files (run with --maintainer)")
        if inv.is_candidate_verdict(x):          # packet e: a candidate family ruled out
            if x["candidate"].strip().lower() not in fams:
                W(fn, n, f"candidate {x['candidate']} was not a lead in the queue (expected for something found while exploring; otherwise check the reference)")
            v = x.get("verdict", "")
            if not (v in ("not_place_data", "out_of_scope", "not_a_dataset", "restricted", "blocked") or v.startswith("duplicate_of:")):
                E(fn, n, "verdict must be not_place_data, out_of_scope, not_a_dataset, restricted, blocked or duplicate_of:<id>")
            if v.startswith("duplicate_of:") and v.split(":", 1)[1] not in IDS:
                E(fn, n, f"{v}: no such inventory id")
            if not x.get("ev") or not urls_ok(x["ev"]):
                E(fn, n, "a verdict needs ev: the URL you read")
            continue
        i = x.get("id", "")
        if not i:
            E(fn, n, "missing 'id' (or 'candidate' for a verdict)")
            continue
        if i in seen:
            E(fn, n, f"{i} appears twice in this file")
        seen.add(i)
        touched[i] = fn
        if not x.get("ev") or not urls_ok(x["ev"]):
            E(fn, n, "ev must be the URL(s) you read, separated by ';'")
        s = x.get("set", {})
        if x.get("new"):
            if x.get("packet") not in ("a", "e", "m"):
                E(fn, n, "new rows only in packets a and e")
            if i in IDS:
                E(fn, n, f"{i} already exists; drop 'new' and update it")
            if not re.match(r"^[a-z0-9]+(_[a-z0-9.]+)+$", i):
                E(fn, n, "id should be <country>_<publisher>_<product>, lowercase with underscores")
            for k in ("dataset_name", "organization", "site_url", "category", "region"):
                if not s.get(k):
                    E(fn, n, f"new row needs '{k}'")
            if s.get("round") != "contrib" and not MAINT:
                E(fn, n, "new rows set round = contrib")
            q = inv.norm_title(s.get("dataset_name", ""))
            best = max(((difflib.SequenceMatcher(None, q, inv.norm_title(r["dataset_name"])).ratio(), r["id"]) for r in rows), default=(0, ""))
            if best[0] >= 0.8:
                W(fn, n, f"possible duplicate of {best[1]} (title similarity {best[0]:.2f})")
            dd = inv.all_dois(json.dumps(s))
            for r in rows:
                if dd and dd & inv.all_dois(" ".join(r.get(k, "") for k in ("persistent_id", "site_url", "access_url", "notes"))):
                    E(fn, n, f"same DOI as {r['id']}: update that row instead")
                    break
        elif i not in IDS:
            E(fn, n, f"unknown id {i}")
        for k, v in s.items():
            if k not in COLS and not MAINT:
                E(fn, n, f"unknown column {k}")
            if k in PROTECTED and not (k == "round" and x.get("new")) and not MAINT:
                E(fn, n, f"{k} is computed or fixed; don't set it")
            if re.fullmatch(r"chk_[a-z0-9_]+", k) and not k.endswith(("_detail", "_evidence")):
                if v not in VOCAB:
                    E(fn, n, f"{k} = {v!r}; use pass/warn/fail/n.a./not_checked")
                if v in ("pass", "warn", "fail"):
                    if k + "_evidence" in COLS and not s.get(k + "_evidence"):
                        E(fn, n, f"{k} set without {k}_evidence")
                    if k + "_detail" in COLS and not s.get(k + "_detail"):
                        W(fn, n, f"{k} has no {k}_detail")
            if k.endswith("_evidence") and v and not urls_ok(v):
                E(fn, n, f"{k} must be URLs")
            if k in ("tier_cap", "browser_tier") and not MAINT and x.get("packet") != "d":
                E(fn, n, f"{k} is set by a maintainer or a person-read (packet d)")
        if s.get("finest_unit_confirmed"):
            for u in re.split(r"[;,]\s*", s["finest_unit_confirmed"]):
                if u and u not in UNITS and not re.fullmatch(r"grid_[0-9.]+(m|km|deg)", u):
                    E(fn, n, f"unit {u!r} not in method/unit-vocabulary.csv (propose the term in your PR text instead)")
        if s.get("license_class") and s["license_class"] not in LIC:
            E(fn, n, f"license_class {s['license_class']!r} not one of {sorted(LIC)}")
        if s.get("license_class") == "public_domain_us_federal" and ".gov" not in (s.get("chk_license_evidence", "") + x.get("ev", "")).lower():
            E(fn, n, "the federal rule needs a .gov evidence page")
        if x.get("packet") == "c" and not x.get("blocked"):
            p = os.path.join(inv.LEDGER, "packets", f"{i}.json")
            if not os.path.exists(p):
                E(fn, n, f"packet c needs ledger/packets/{i}.json")
            else:
                try:
                    pk = json.load(open(p, encoding="utf-8"))
                    miss = [k for k in PACKET_KEYS if k not in pk]
                    if miss:
                        E(fn, n, f"packets/{i}.json missing {miss}")
                    if not (isinstance(pk.get("place_key"), dict) and pk["place_key"].get("system")):
                        W(fn, n, f"packets/{i}.json: place_key.system missing")
                except json.JSONDecodeError as e:
                    E(fn, n, f"packets/{i}.json not JSON: {e}")
    # does it apply cleanly on top of everything else?
    try:
        inv.apply_file([dict(r) for r in rows], list(cols), path)
    except Exception as e:  # noqa: BLE001
        E(fn, 0, f"does not apply: {e}")

# overlap: rows changed on the target branch since this branch started
if against:
    try:
        mb = git("merge-base", "HEAD", against).strip()
        theirs = [p for p in git("diff", "--name-only", "--diff-filter=AM", mb, against, "--", "ledger/").split() if p.endswith(".jsonl")]
        for p in theirs:
            for line in git("show", f"{against}:{p}").splitlines():
                if line.strip():
                    i = json.loads(line).get("id")
                    if i in touched:
                        E(touched[i], 0, f"{i} was changed on {against} since you branched ({os.path.basename(p)}): re-check it, then rebase")
    except subprocess.CalledProcessError as e:
        W("git", 0, f"overlap check skipped: {e.stderr.strip()[:200]}")

for w in warns:
    print("warn ", w)
for e in errs:
    print("ERROR", e)
print(f"{len(paths)} file(s): {len(errs)} errors, {len(warns)} warnings")
sys.exit(1 if errs else 0)
