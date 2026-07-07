"""Shared: the human's Bash(...) allowlist from permissions.allow.

Single source of truth for both bash-guard.py (what it lets through) and
solve-init.py (what the agent is told it may run) — so the two never drift.
"""
import json
import os
import subprocess


def repo_root(cwd):
    r = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else cwd


def allow_patterns(cwd):
    """Bash(...) globs from permissions.allow (global + project settings)."""
    pats = []
    for fp in (
        os.path.expanduser("~/.claude/settings.json"),
        os.path.join(repo_root(cwd), ".claude", "settings.json"),
        os.path.join(repo_root(cwd), ".claude", "settings.local.json"),
    ):
        try:
            allow = json.load(open(fp)).get("permissions", {}).get("allow", [])
        except (OSError, ValueError, AttributeError):
            continue
        pats += [e[5:-1] for e in allow if isinstance(e, str) and e.startswith("Bash(") and e.endswith(")")]
    return pats


def add_pattern(fp, glob):
    try:
        data = json.load(open(fp))
    except (OSError, ValueError):
        data = {}
    allow = data.setdefault("permissions", {}).setdefault("allow", [])
    entry = f"Bash({glob})"
    if entry in allow:
        return False
    allow.append(entry)
    os.makedirs(os.path.dirname(fp) or ".", exist_ok=True)
    with open(fp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return True


def remove_pattern(fp, glob):
    try:
        data = json.load(open(fp))
    except (OSError, ValueError):
        return False
    allow = data.get("permissions", {}).get("allow", [])
    entry = f"Bash({glob})"
    if entry not in allow:
        return False
    allow.remove(entry)
    with open(fp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return True


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(prog="solve-allow")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="print the Bash allowlist for the current repo")
    a = sub.add_parser("add", help="add a Bash(<glob>) entry to a settings file")
    a.add_argument("glob")
    a.add_argument("--file", default=".claude/settings.local.json")
    r = sub.add_parser("remove", help="remove a Bash(<glob>) entry from a settings file")
    r.add_argument("glob")
    r.add_argument("--file", default=".claude/settings.local.json")
    args = ap.parse_args()

    if args.cmd == "list":
        for pat in allow_patterns(os.getcwd()):
            print(pat)
    elif args.cmd == "add":
        changed = add_pattern(args.file, args.glob)
        print(f"{'added' if changed else 'already present'}: Bash({args.glob}) -> {args.file}")
    elif args.cmd == "remove":
        changed = remove_pattern(args.file, args.glob)
        print(f"{'removed' if changed else 'not present'}: Bash({args.glob}) -> {args.file}")
