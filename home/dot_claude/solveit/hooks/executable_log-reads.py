#!/usr/bin/env python3
"""SolveIt PreToolUse logger for Read / Grep / Glob.

Appends one line per read/search to <repo-root>/.solve/reads.log (git-excluded)
so the human can see what the agent is looking at and manage context. Never
blocks (always exits 0); fails silently on any error.
"""
import datetime
import json
import os
import subprocess
import sys


def repo_root(cwd):
    r = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else cwd


def solve_dir(cwd):
    """<repo-root>/.solve — where reads.log lives (git-excluded)."""
    return os.path.join(repo_root(cwd), ".solve")


def target_for(tool, ti):
    if tool == "Read":
        return ti.get("file_path", "")
    if tool == "Glob":
        t = ti.get("pattern", "")
        return f"{t}  (in {ti['path']})" if ti.get("path") else t
    if tool == "Grep":
        t = ti.get("pattern", "")
        extra = []
        if ti.get("path"):
            extra.append(ti["path"])
        if ti.get("glob"):
            extra.append(f"glob={ti['glob']}")
        return f"{t}  ({', '.join(extra)})" if extra else t
    return ""


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    if tool not in ("Read", "Grep", "Glob"):
        return
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    target = target_for(tool, ti)

    logdir = solve_dir(cwd)
    os.makedirs(logdir, exist_ok=True)
    ts = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(os.path.join(logdir, "reads.log"), "a") as f:
        f.write(f"{ts}\t{tool}\t{target}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)  # never blocks
