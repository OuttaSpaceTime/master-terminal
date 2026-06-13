#!/usr/bin/env python3
"""SolveIt PreToolUse guard for Write / Edit / MultiEdit.

Blocks (exit 2, message to stderr) when:
  1. a single edit adds more than 20 lines  -> split into a smaller step;
  2. a 5th numbered work file (NN-*) is added to a .claude/tasks/<name>/ folder
     -> checkpoint due, commit the folder and start a new one;
  3. 20+ added lines are already uncommitted in the file's enclosing git repo
     -> checkpoint due, the human commits before more is written.

20 lines is a hard ceiling, not a target. Fails open: any internal error
allows the tool call so a bug here never wedges a session.
"""
import json
import os
import re
import subprocess
import sys

CAP = 20
NUMBERED = re.compile(r"^\d{2}[-_.]")


def nlines(s):
    return len(s.splitlines()) if s else 0


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True
    )


def deny(msg):
    sys.stderr.write(msg)
    sys.exit(2)


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()

    fp = ti.get("file_path")
    if not fp:
        return
    if not os.path.isabs(fp):
        fp = os.path.normpath(os.path.join(cwd, fp))

    # 1. per-operation size: how many lines does this single step add?
    if tool == "Write":
        added = nlines(ti.get("content", ""))
    elif tool == "Edit":
        added = max(0, nlines(ti.get("new_string", "")) - nlines(ti.get("old_string", "")))
    elif tool == "MultiEdit":
        added = sum(
            max(0, nlines(e.get("new_string", "")) - nlines(e.get("old_string", "")))
            for e in ti.get("edits", [])
        )
    else:
        added = 0
    if added > CAP:
        deny(
            f"SolveIt: this step adds {added} lines (hard ceiling {CAP}). "
            f"That ceiling is not a target — make a genuinely small change, "
            f"one idea at a time, and hand it back to verify."
        )

    # 2. four-file cap inside a task folder
    parts = fp.split(os.sep)
    if ".claude" in parts:
        i = parts.index(".claude")
        if i + 2 < len(parts) and parts[i + 1] == "tasks":
            task_dir = os.sep.join(parts[: i + 3])
            base = os.path.basename(fp)
            if NUMBERED.match(base) and not os.path.exists(fp):
                try:
                    existing = [
                        f
                        for f in os.listdir(task_dir)
                        if NUMBERED.match(f)
                        and os.path.isfile(os.path.join(task_dir, f))
                    ]
                except FileNotFoundError:
                    existing = []
                if len(existing) >= 4:
                    deny(
                        "SolveIt: this task folder already holds 4 work files (01-04). "
                        "Checkpoint due - ask the human to commit this task folder "
                        "(its own repo), then start a new dated folder under "
                        ".claude/tasks/ for the next steps."
                    )

    # 3. cumulative uncommitted added lines in the enclosing repo
    d = os.path.dirname(fp) or cwd
    top = git(d, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return
    repo = top.stdout.strip()

    total = 0
    if git(repo, "rev-parse", "--verify", "-q", "HEAD").returncode == 0:
        for line in git(repo, "diff", "--numstat", "HEAD").stdout.splitlines():
            col = line.split("\t", 1)[0]
            if col.isdigit():
                total += int(col)
    others = git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout
    for rel in filter(None, others.split("\0")):
        try:
            with open(os.path.join(repo, rel), "r", errors="ignore") as fh:
                total += sum(1 for _ in fh)
        except OSError:
            pass

    if total >= CAP:
        deny(
            f"SolveIt: {total} lines are already uncommitted in {repo}. "
            f"Checkpoint due before writing more - tell the human what to commit "
            f"and why, then stop. You do not commit; the human does."
        )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open
