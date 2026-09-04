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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solve_allow import allow_patterns

CONTEXT = """\
SolveIt is on (the default). Work in small, verifiable steps; the human runs and
commits. Follow this and you will never hit a guard hook:
- NOTHING IS WRITTEN OR RUN WITHOUT A GO: the human's message must open with an
  affirmation (go, ok, yes, ja, do it, apply, ...). Without one, plan and discuss
  only — name the change, show the exact diff they could apply, and stop. A go
  covers only the turn it opens.
- SKETCH BEFORE YOU WRITE: every change to project code is shown as a diff in chat
  first, then you stop — the human types it themselves, or answers go and you apply
  exactly that diff. ONE project file lands per go, then hand back. A script under
  .solve/tasks/ you write straight away, but it does NOT run in the same turn: say
  what it does, show it, hand over `▶ nvim <path>`, stop — their next go runs it.
- EXPLORE with Read/Grep/Glob, OR read-only shell (grep, rg, find, ls, cat, head,
  awk, ...) and read-only git (diff/status/log/show/blame/ls-files). Both are
  logged to .solve/reads.log, never blocked. No output redirection, no find -exec.
- RUN code only as a task script: write a script under
  .solve/tasks/<YYYY-MM-DD>-<name>/ whose first comment line is exactly how to run it
  (at most 1-3 comment lines total, no README needed), hand it over, and run it bare
  on the next go (the script path is the last token, no args). Re-running an unchanged
  script is free. .solve/ is git-excluded, so scratch never dirties the repo.
- HAND OVER SINGLE-LINE COMMANDS: every command you give the human to run must fit on
  one line (they copy it from chat; multi-line mangles on paste). Join with && or ;,
  never a backslash continuation or multi-line bash fence. A Stop hook enforces this.
- NEVER COMMIT anything — not the main repo, not scratch. Leave changes DIRTY so
  the human verifies and commits. Checkpoints: stage at 30 unstaged lines, a
  warning fires at 150 total, a hard block at 300 total forces a commit — say what
  changed and why, then stop.
- KEEP STEPS SMALL: at most 30 added lines per edit; after each step, hand control
  back to the human. Propose the next step as a diff sketch — never a multi-step plan.
- The allowlist below can change mid-session — run `solve-allow list` any time to
  see the current one. Use the solve-allow skill to add an allowance, solve-baseline
  to curate a repo's baseline validation commands.
- YOU verify, the human never reports back: check the output/file/test yourself and
  say in one line what you saw. Never ask them to paste output or confirm before you
  continue. The probe you hand over (`▶ Try: <cmd>`) is theirs to run for their own
  understanding; `▶ Verify:` is only for something you already ran.
"""

GO_WORDS = (
    "go", "ok", "okay", "yes", "yep", "yeah", "sure", "ja", "jep", "passt",
    "los", "mach", "do it", "go ahead", "apply", "ship it", "make it so",
)


def is_go(prompt):
    words = prompt.strip().lower().replace(",", " ").split()
    return bool(words) and (words[0] in GO_WORDS or " ".join(words[:2]) in GO_WORDS)


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def main():
    if os.environ.get("SOLVEIT_OFF"):
        return
    data = json.load(sys.stdin)
    session = data.get("session_id") or "nosession"
    cwd = data.get("cwd") or os.getcwd()

    state_dir = os.path.expanduser("~/.claude/solveit/state")
    os.makedirs(state_dir, exist_ok=True)
    open(os.path.join(state_dir, f"{session}.edits"), "w").write("0\n")
    go = os.path.join(state_dir, f"{session}.go")
    if is_go(data.get("prompt") or ""):
        open(go, "w").write("1\n")
    elif os.path.exists(go):
        os.remove(go)
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

    with open(marker, "w") as f:
        f.write("1\n")

    context = CONTEXT
    patterns = allow_patterns(cwd)
    if patterns:
        allowed = ", ".join(f"`{p}`" for p in patterns)
        context += (
            "\nALLOWLISTED for this repo — you may run these directly (they "
            f"bypass the Bash jail): {allowed}\n"
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)  # never blocks
