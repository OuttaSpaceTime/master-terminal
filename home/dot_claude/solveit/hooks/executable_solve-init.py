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
A SolveIt session is starting. A fresh solve.md (Polya's four steps) was created and committed at:
  {rel}
Its folder {folder_rel} is already its own git repo with the scaffold committed — it starts clean.

How you work here — follow this and you will never hit a guard hook:
- EXPLORE with the Read/Grep/Glob tools when present, OR with read-only shell (grep, rg, find, ls,
  cat, head, ...) — both are fine and both are logged to reads.log, never blocked. (Grep/Glob can
  be dropped by a tool-registration bug; the shell commands always work.) Do NOT wrap a search in a
  task script — searching is not "running". Read-only search may not redirect to a file or run
  find -exec/-delete; if you need to produce or mutate, that is a task script.
- INSPECT git directly: git diff/status/log/show/blame/ls-files/... are allowed (and logged) for
  looking at changes. You may `git init` a task folder (to make it its own scratch repo). Everything
  else that touches git is blocked — add, commit, --amend, checkout, reset, stash, apply, ...
- RUN code only as a task script: write a script plus a .md describing it under {folder_rel}/, then
  run it as one task-script Bash command. Read-only search/inspection (incl. for/while/if loops over
  grep/find/awk/...) is fine; ad-hoc mutating commands are not.
- NEVER COMMIT anything — not the main repo, not your task/scratch folders, not at all. The whole
  philosophy is to leave changes DIRTY so the human verifies and commits them. When a checkpoint is
  due (20 uncommitted lines, in EITHER the main repo or a scratch repo), say what changed and why,
  then stop and hand control back — the human runs every commit.
- KEEP STEPS SMALL: at most 20 added lines per edit, and after each step stop and hand control back.

First, greet the human in one line and treat their message as the problem to solve (if it is not a
problem statement yet, ask "What do you want to solve?"). Once the problem is clear, rename THIS
existing folder with `mv` — do not create a new folder and do not rewrite solve.md:
  mv {folder_rel} .claude/tasks/{date}-<short-slug>
then, in that SAME first answer, hand them the commands to open the scratch folder and edit solve.md
themselves (they run these — you do not):
  cd .claude/tasks/{date}-<short-slug>
  nvim .claude/tasks/{date}-<short-slug>/solve.md

solve.md is the HUMAN'S document and the session's source of truth. Do NOT write or append to it on
your own — not the problem statement, not findings, not a plan. The human writes it; you hand over
the `nvim <path>` and let them. Edit solve.md ONLY when the human explicitly asks you to, and then in
small edits. Report findings and observations to the human in chat instead — and speak up there when
a step's assumptions break, when we should drop back to an earlier Polya step, or when new work
contradicts the document. Do not silently edit solve.md to "keep it in sync".
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
    # reads.log lives inside this scratch folder; keep it out of the folder's own
    # git repo so it never counts toward the 20-line cap or shows up to commit.
    sx = os.path.join(folder, ".git", "info", "exclude")
    try:
        os.makedirs(os.path.dirname(sx), exist_ok=True)
        with open(sx, "a") as f:
            f.write("reads.log\n")
    except OSError:
        pass
    # Commit the scaffold so the folder's own repo starts at a clean baseline.
    # Otherwise the edit-guard's uncommitted-line cap trips on the very first
    # write into the folder (the 30+ line solve.md). The agent owns this scratch
    # repo, so an explicit identity keeps the commit working with no global config.
    run("git", "-C", folder, "add", "-A")
    run("git", "-C", folder,
        "-c", "user.name=SolveIt", "-c", "user.email=solveit@localhost",
        "commit", "-q", "-m", "solve: scaffold")

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

    # Marker stores the scratch FOLDER (absolute). The log hooks read it to write
    # reads.log inside the session's scratch folder; bash-guard rewrites it when the
    # agent renames the folder, so the log follows the rename.
    os.makedirs(state_dir, exist_ok=True)
    with open(marker, "w") as f:
        f.write(os.path.realpath(folder) + "\n")

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
