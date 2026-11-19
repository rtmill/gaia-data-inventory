#!/usr/bin/env python3
"""Self-test of the contribution machinery, on a throwaway copy (run from the repo root; CI runs it on every push and PR).

Proves, against the ledger as it is right now: the whole ledger rebuilds; a clean contribution passes the check;
a contribution with errors is rejected and the errors are named; and a contribution that touches a dataset changed
on main since it branched is rejected. Exit 1 if any of these is not so.
"""
import csv, json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
tmp = os.path.join(tempfile.mkdtemp(prefix="inv-selftest-"), "repo")
shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns(".git", "__pycache__", ".inventory-discarded"))
fails = []


def sh(*a, ok=None):
    p = subprocess.run(a, cwd=tmp, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def check(name, cond, out=""):
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond:
        fails.append(name)
        print("      " + out.strip().replace("\n", "\n      ")[-1500:])


def git(*a):
    return sh("git", "-c", "user.name=selftest", "-c", "user.email=selftest@example.invalid", *a)


py = sys.executable
git("init", "-q", "-b", "main")
git("add", "-A")
git("commit", "-qm", "main")

rc, out = sh(py, "scripts/build.py")
check("the whole ledger rebuilds", rc == 0, out)

rows = list(csv.DictReader(open(os.path.join(tmp, "build", "inventory-all.csv"), encoding="utf-8")))
rid = next(r["id"] for r in rows if r["verify_tier"] == "Bronze")
rec = lambda note, **s: json.dumps({"id": rid, "by": "selftest", "packet": "b", "ev": "https://example.org/page", "note": note, "set": s}) + "\n"
good = rec("clean", chk_license="pass", chk_license_detail="CC BY 4.0", chk_license_evidence="https://example.org/licence", license_confirmed="CC BY 4.0", license_class="open")

git("switch", "-qc", "contrib")
open(os.path.join(tmp, "ledger", "2099-01-01-selftest-good.jsonl"), "w", encoding="utf-8").write(good)
git("add", "-A"); git("commit", "-qm", "good")
rc, out = sh(py, "scripts/validate.py", "--changed", "--against", "main")
check("a clean contribution passes", rc == 0 and "0 errors" in out, out)

open(os.path.join(tmp, "ledger", "2099-01-01-selftest-bad.jsonl"), "w", encoding="utf-8").write(rec("bad", chk_unit="good", verify_tier="Gold"))
rc, out = sh(py, "scripts/validate.py", "ledger/2099-01-01-selftest-bad.jsonl")
check("a bad contribution is rejected, with both errors named", rc == 1 and "chk_unit" in out and "verify_tier" in out and "Traceback" not in out, out)
os.remove(os.path.join(tmp, "ledger", "2099-01-01-selftest-bad.jsonl"))

git("switch", "-q", "main")
open(os.path.join(tmp, "ledger", "2099-01-01-other-first.jsonl"), "w", encoding="utf-8").write(rec("someone else got there first", chk_temporal="pass", chk_temporal_detail="2010-2024", chk_temporal_evidence="https://example.org/years", temporal_confirmed="2010-2024"))
git("add", "-A"); git("commit", "-qm", "someone else")
git("switch", "-q", "contrib")
rc, out = sh(py, "scripts/validate.py", "--changed", "--against", "main")
check("a contribution overlapping a change on main is rejected", rc == 1 and "was changed on main since you branched" in out, out)

shutil.rmtree(os.path.dirname(tmp), ignore_errors=True)
print("\nself-test passed" if not fails else f"\n{len(fails)} self-test failure(s)")
sys.exit(1 if fails else 0)
