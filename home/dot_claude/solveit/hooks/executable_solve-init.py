#!/usr/bin/env python3
"""SolveIt SessionStart hook (matcher: startup).

On a new session: create a fresh per-session task folder containing a
Polya-structured solve.md, make that folder its own git repo, ensure the main
repo ignores .claude task artifacts, and tell Claude to ask the human what they
want to solve. Fails open: prints nothing and exits 0 on any error.
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
A SolveIt session has started. A fresh solve.md (Polya's four steps) was created at:
  {rel}

Before anything else, greet the human in one line and ask: "What do you want to solve?"
Tell them they can write directly in it — `nvim {rel}` — and that it guides the whole session.
Keep solve.md as the source of truth: help refine it in small edits when asked, and speak up
when a step's assumptions break, when we should drop back to an earlier Polya step, or when new
work contradicts what the document says.
"""


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def main():
    data = json.load(sys.stdin)
    if data.get("source") not in (None, "startup"):
        return
    cwd = data.get("cwd") or os.getcwd()

    top = run("git", "-C", cwd, "rev-parse", "--show-toplevel")
    in_repo = top.returncode == 0
    root = top.stdout.strip() if in_repo else cwd

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    folder = os.path.join(root, ".claude", "tasks", f"{stamp}-solve")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "solve.md")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(SCAFFOLD)

    # the session folder is its own git repo
    if not os.path.isdir(os.path.join(folder, ".git")):
        run("git", "init", "-q", folder)

    # main repo ignores task artifacts (local, append-only, non-destructive)
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

    rel = os.path.relpath(path, cwd)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": CONTEXT.format(rel=rel),
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)  # never blocks startup
