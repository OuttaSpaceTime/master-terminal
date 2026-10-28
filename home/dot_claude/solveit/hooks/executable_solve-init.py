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
SolveIt is on (the default). Work step by step, like a walkthrough; the human reads
along and commits. Follow this and you will never hit a guard hook:
- ONE STEP PER TURN: take the smallest step that moves the work on — at most one
  project file and 30 added lines — then hand back. No go is needed; the caps stop
  a turn that tries to do too much.
- EVERY STEP WRITES ITS CHECK TO current.<ext>, AND THE HUMAN RUNS IT: archive the
  previous script under a numbered descriptive name (mv), write a fresh
  .solve/tasks/<YYYY-MM-DD>-<name>/current.<ext> that checks this step, hand over
  its one-line run command prefixed with `!` (fenced), and stop. First comment
  line = exactly how to run it; then a short outline: what changed, what it
  checks, what to look at in the output. You never run current.<ext> yourself.
  Their `!` output lands in the transcript and starts a turn: quote the lines that
  matter, name the next step, and stop. A project edit is blocked until they have
  run the current.<ext> you wrote before their last message.
- EXPLORE with Read, OR read-only shell (grep, rg, find, ls, cat, head, sed -n,
  awk, ...) and read-only git (diff/status/log/show/blame/ls-files, worktree list,
  branch --show-current, remote -v, config --get). Both are logged to
  .solve/reads.log, never blocked. No output redirection, no find -exec.
- RUN code only as a task script, bare (the script path is the last token, no
  args), never current.<ext>. Re-running an unchanged archived script is free. .solve/ is git-excluded, so
  scratch never dirties the repo.
- SINGLE-LINE COMMANDS: any command you show the human must fit on one line (they
  copy it from chat; multi-line mangles on paste). Join with && or ;, never a
  backslash continuation or multi-line bash fence. A Stop hook enforces this.
- NEVER COMMIT anything — not the main repo, not scratch. Leave changes DIRTY so
  the human verifies and commits. Checkpoints: stage at 30 unstaged lines, a
  warning fires at 150 total, a hard block at 300 total forces a commit — say what
  changed and why, then stop.
- SUBAGENTS only when the human asks to hand a mechanical task to one. A subagent
  runs outside these guards and the caps. Brief it to commit in small steps as it
  goes (one short single-line message each, no trailer, never amend, never push)
  and to report its commit list; you then resume the slow steps.
- The allowlist below can change mid-session — run `solve-allow list` any time to
  see the current one. Use the solve-allow skill to add an allowance, solve-baseline
  to curate a repo's baseline validation commands.
- The human never reports back: their `!` output is in the transcript. Never ask
  them to paste output or tell you what they see.
"""

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
