#!/usr/bin/env python3
"""Check that this machine can contribute, and say exactly what to do if it can't (run from the repo root).

    python scripts/preflight.py

Checks: git and its identity, the GitHub CLI (gh) and that it is signed in, that the signed-in account can push to this
repository, and that the folder is a clone of it. Exit 0 if ready, 1 if something needs doing. Nothing is changed.
"""
import json, platform, shutil, subprocess, sys

REPO = "rtmill/gaia-data-inventory"
todo, ok = [], []


def run(*a):
    try:
        p = subprocess.run(a, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


if not shutil.which("git"):
    todo.append("Git is not installed. Install it from https://git-scm.com/downloads, then reopen the terminal.")
else:
    name, email = run("git", "config", "user.name")[1], run("git", "config", "user.email")[1]
    if name and email:
        ok.append(f"git identity: {name} <{email}>")
    else:
        todo.append('Git doesn\'t know who you are. Run:\n      git config --global user.name "Your Name"\n      git config --global user.email "you@example.org"')
    rc, url = run("git", "remote", "get-url", "origin")
    if rc or REPO.lower() not in url.lower():
        todo.append(f"This folder is not a clone of {REPO}. Run:\n      git clone https://github.com/{REPO}\n      cd gaia-data-inventory")
    else:
        ok.append("this folder is a clone of the repository")

if not shutil.which("gh"):
    how = {"Windows": "winget install --id GitHub.cli", "Darwin": "brew install gh"}.get(platform.system(), "see https://cli.github.com (packages for every Linux distribution)")
    todo.append(f"The GitHub CLI (gh) is not installed. Claude uses it to reserve your work and submit it. Install it:\n      {how}\n    then close and reopen the terminal, and run:\n      gh auth login")
else:
    rc, out = run("gh", "api", "user", "--jq", ".login")
    if rc:
        todo.append("The GitHub CLI is installed but not signed in. In a normal terminal (not inside Claude Code) run:\n      gh auth login\n"
                    "    Choose GitHub.com, HTTPS, \"Yes\" to authenticate Git, and sign in through the browser with the account that was given access.")
    else:
        login = out.splitlines()[-1]
        rc, perm = run("gh", "api", f"repos/{REPO}", "--jq", ".permissions.push")
        if rc == 0 and perm.strip() == "true":
            ok.append(f"signed in to GitHub as {login}, with write access")
            rc, helper = run("git", "config", "--get-all", "credential.https://github.com.helper")
            if "gh" not in helper:
                todo.append("Git is not set up to push with your GitHub sign-in. Run:\n      gh auth setup-git")
        else:
            todo.append(f"You are signed in to GitHub as {login}, but that account can't write to {REPO}.\n"
                        f"    If you have another account that was given access, switch to it:\n      gh auth login      (or: gh auth switch)\n"
                        f"    Otherwise ask Robert (rtmill) to add {login} as a collaborator, accept the invitation at https://github.com/{REPO}/invitations, and run this again.")

for o in ok:
    print("ok   ", o)
for n, t in enumerate(todo, 1):
    print(f"TO DO {n}. {t}")
print("\nReady to contribute." if not todo else f"\n{len(todo)} thing(s) to do, then run this again: python scripts/preflight.py")
sys.exit(1 if todo else 0)
