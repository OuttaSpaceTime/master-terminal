#!/usr/bin/env python3
"""SolveIt UserPromptSubmit hook — create solve.md on the first prompt.

Runs on every user prompt but acts only once per session (guarded by a marker
keyed on session_id), so idle launches never litter the repo. On the first
prompt it creates a per-session task folder with a Polya-structured solve.md,
git-inits it, ignores .claude task artifacts in the main repo, and injects
context telling Claude to greet, treat the message as the problem, and rename
the folder to a descriptive name once the problem is clear.
Fails open: prints nothing and exits 0 on any error.
"""
import datetime
import json
import os
import subprocess
import sys

SCAFFOLD = """\
# Solve

> **What do you want to solve?** Write it below in your own words, then we work through it together.

## Problem

<one or two sentences — what are you actually trying to do?>

## 1. Understand the problem

- What exactly is being asked? What are the inputs, and the desired outputs?
- What does success look like — how will you know it works?
- Restate it in your own words. Work one concrete example by hand.
- What are the constraints, the unknowns, and the assumptions?

## 2. Devise a plan

- What is the smallest first step that produces something verifiable?
- Have you seen a similar problem? What pattern, tool, or prior art fits?
- Break it into pieces — which piece is riskiest or most uncertain?
- What would a test for the first step look like?

## 3. Carry out the plan

- One small step at a time; verify each before the next.
- (steps, decisions, and notes accumulate here as we go)

## 4. Look back

- Does the result actually solve the problem? Check it against your success criteria.
- What surprised you? What would you do differently?
- Anything to simplify now that it works?
"""

CONTEXT = """\
A SolveIt session is starting. A fresh solve.md (Polya's four steps) was created at:
  {rel}

Greet the human in one line and treat their message as the problem to solve (if it is not a
problem statement yet, ask "What do you want to solve?"). Once the problem is clear, rename THIS
existing folder with `mv` — do not create a new folder and do not rewrite solve.md:
  mv {folder_rel} .claude/tasks/{date}-<short-slug>
then point them at `nvim .claude/tasks/{date}-<short-slug>/solve.md`.

solve.md is the session's source of truth: refine it in small edits when asked, and speak up when
a step's assumptions break, when we should drop back to an earlier Polya step, or when new work
contradicts what the document says.
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
    in_repo = top.returncode == 0
    root = top.stdout.strip() if in_repo else cwd

    now = datetime.datetime.now()
    folder = os.path.join(root, ".claude", "tasks", now.strftime("%Y-%m-%d-%H%M%S") + "-solve")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "solve.md")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(SCAFFOLD)

    if not os.path.isdir(os.path.join(folder, ".git")):
        run("git", "init", "-q", folder)

    if in_repo:
        exclude = os.path.join(root, ".git", "info", "exclude")
        try:
            existing = open(exclude).read() if os.path.exists(exclude) else ""
            add = [p for p in (".claude/tasks/", ".claude/solveit/") if p not in existing]
            if add:
                os.makedirs(os.path.dirname(exclude), exist_ok=True)
                with open(exclude, "a") as f:
                    if existing and not existing.endswith("\n"):
                        f.write("\n")
                    f.write("\n".join(add) + "\n")
        except OSError:
            pass

    os.makedirs(state_dir, exist_ok=True)
    with open(marker, "w") as f:
        f.write(path + "\n")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": CONTEXT.format(
                rel=os.path.relpath(path, cwd),
                folder_rel=os.path.relpath(folder, cwd),
                date=now.strftime("%Y-%m-%d"),
            ),
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)  # never blocks
