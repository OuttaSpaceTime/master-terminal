#!/usr/bin/env python3
"""SolveIt UserPromptSubmit hook — per-repo setup, once per session.

Runs on every user prompt but acts only once per session (guarded by a marker
keyed on session_id). On the first prompt it adds .solve/ to the repo's
.git/info/exclude (local, untracked — so the agent's scratch area and reads.log
never dirty the tree) and injects a short reminder of how SolveIt Bash/edit
guards work, so the agent stays inside them.
Fails open: prints nothing and exits 0 on any error.
"""
import json
import os
import subprocess
import sys

CONTEXT = """\
SolveIt is on (the default). Work in small, verifiable steps; the human runs and
commits. Follow this and you will never hit a guard hook:
- EXPLORE with Read/Grep/Glob, OR read-only shell (grep, rg, find, ls, cat, head,
  awk, ...) and read-only git (diff/status/log/show/blame/ls-files). Both are
  logged to .solve/reads.log, never blocked. No output redirection, no find -exec.
- RUN code only as a task script: write a script plus a .md describing it under
  .solve/tasks/<YYYY-MM-DD>-<name>/, then run it bare (the script path is the last
  token, no args). At most 4 numbered files per folder. .solve/ is git-excluded,
  so scratch never dirties the repo.
- NEVER COMMIT anything — not the main repo, not scratch. Leave changes DIRTY so
  the human verifies and commits. When a checkpoint is due (20 unstaged / 60 total
  uncommitted lines), say what changed and why, then stop.
- KEEP STEPS SMALL: at most 20 added lines per edit; after each step, hand control
  back to the human. Do not propose the next step unless asked.
"""


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def main():
    data = json.load(sys.stdin)
    session = data.get("session_id") or "nosession"
    cwd = data.get("cwd") or os.getcwd()

    state_dir = os.path.expanduser("~/.claude/solveit/state")
    marker = os.path.join(state_dir, f"{session}.solve")
    if os.path.exists(marker):
        return  # already initialised this session

    top = run("git", "-C", cwd, "rev-parse", "--show-toplevel")
    if top.returncode == 0:
        root = top.stdout.strip()
        exclude = os.path.join(root, ".git", "info", "exclude")
        try:
            existing = open(exclude).read() if os.path.exists(exclude) else ""
            if ".solve/" not in existing:
                os.makedirs(os.path.dirname(exclude), exist_ok=True)
                with open(exclude, "a") as f:
                    if existing and not existing.endswith("\n"):
                        f.write("\n")
                    f.write(".solve/\n")
        except OSError:
            pass

    os.makedirs(state_dir, exist_ok=True)
    with open(marker, "w") as f:
        f.write("1\n")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": CONTEXT,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)  # never blocks
