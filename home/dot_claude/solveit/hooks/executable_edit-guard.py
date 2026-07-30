#!/usr/bin/env python3
"""SolveIt PreToolUse guard for Write / Edit / MultiEdit.

Blocks (exit 2, message to stderr) when:
  1. a single edit adds more than 30 lines  -> split into a smaller step;
  2. uncommitted work in the file's enclosing git repo crosses a cap. Three tiers:
       - DIRTY_CAP (30): unstaged + untracked added lines -> checkpoint due. The
         human stages what they accept (staged lines don't count here, so work
         continues) OR commits. Staging is the "accepted, keep going" signal.
       - WARN_CAP (150): staged + unstaged + untracked added lines -> the write
         still lands (exit 0), but a non-blocking warning is emitted so the human
         wraps up the current commit's goal and commits soon.
       - TOTAL_CAP (300): staged + unstaged + untracked added lines -> the human
         must commit; staging no longer helps. This forces a real commit from
         time to time.
     .solve/ is git-excluded, so task-folder scripts never inflate the main
     repo's count — it tracks real project changes. Each .solve/tasks/<X> folder
     is auto-git-init'd on first write, so it's its own repo with its own separate
     dirty limit. Either way the agent never commits — it stops and the human commits.
  3. a write would create a SECOND .solve/tasks/<X> folder in one session. The
     first task folder written to is recorded per session_id (state file
     ~/.claude/solveit/state/<session>.taskdir); later writes must target that
     same folder — add more scripts there rather than opening a new folder.

30 lines is a hard ceiling per step, not a target. Fails open: any internal
error allows the tool call so a bug here never wedges a session.
"""
import json
import os
import subprocess
import sys

CAP = 30  # per single edit/write
EDIT_CAP = 4  # project-code edits per human turn (reset by solve-init on each prompt)
DIRTY_CAP = 30  # unstaged + untracked -> pause & force stage
WARN_CAP = 150  # staged + unstaged + untracked -> warn, proceed
TOTAL_CAP = 300  # staged + unstaged + untracked -> hard block, force commit


def nlines(s):
    return len(s.splitlines()) if s else 0


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True
    )


def deny(msg):
    sys.stderr.write(msg)
    sys.exit(2)


def warn(msg):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": msg,
        },
        "systemMessage": msg,
    }))


def is_task_repo(repo):
    """True if `repo` is itself a .solve/tasks/<name> folder (the agent's own
    scratch repo) rather than the main project repo. The agent still never
    commits it — the human does — but it gets its own dirty limit."""
    parts = repo.split(os.sep)
    if ".solve" not in parts:
        return False
    i = parts.index(".solve")
    return i + 2 < len(parts) and parts[i + 1] == "tasks"


def task_folder_root(fp):
    """The .solve/tasks/<X> folder a path lives under, or None."""
    parts = fp.split(os.sep)
    if ".solve" not in parts:
        return None
    i = parts.index(".solve")
    if i + 2 < len(parts) and parts[i + 1] == "tasks":
        return os.sep.join(parts[: i + 3])
    return None


def main():
    if os.environ.get("SOLVEIT_OFF"):
        return
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

    # Make each .solve/tasks/<X> folder its own scratch repo so the caps below
    # scope to it (else it resolves up to the git-excluded main repo and never
    # counts). The human still commits it; the agent never does.
    task_root = task_folder_root(fp)
    if task_root:
        session = data.get("session_id") or "nosession"
        marker = os.path.expanduser(f"~/.claude/solveit/state/{session}.taskdir")
        recorded = open(marker).read().strip() if os.path.exists(marker) else ""
        if recorded and recorded != task_root:
            deny(
                f"SolveIt: this session already has one task folder:\n  {recorded}\n"
                f"Add more scripts there — don't create a second one ({task_root}). "
                f"One task folder per Claude Code session."
            )
        if not recorded:
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            open(marker, "w").write(task_root + "\n")
    if not task_root:
        session = data.get("session_id") or "nosession"
        counter = os.path.expanduser(f"~/.claude/solveit/state/{session}.edits")
        n = (int(open(counter).read().strip() or 0) if os.path.exists(counter) else 0) + 1
        os.makedirs(os.path.dirname(counter), exist_ok=True)
        open(counter, "w").write(f"{n}\n")
        if n > EDIT_CAP:
            deny(
                f"SolveIt: {n} edits to project code since the human's last message "
                f"(cap {EDIT_CAP}). One step, then hand back — they verify each change "
                f"before the next one lands."
            )
    if task_root and not os.path.isdir(os.path.join(task_root, ".git")):
        os.makedirs(task_root, exist_ok=True)
        git(task_root, "init", "-q")

    # 2. cumulative uncommitted added lines in the enclosing repo (see docstring)
    d = os.path.dirname(fp) or cwd
    top = git(d, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return
    repo = top.stdout.strip()

    def added_lines(*diff_args):
        n = 0
        for line in git(repo, "diff", "--numstat", *diff_args).stdout.splitlines():
            col = line.split("\t", 1)[0]
            if col.isdigit():
                n += int(col)
        return n

    dirty = added_lines()  # unstaged: working tree vs index
    others = git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout
    for rel in filter(None, others.split("\0")):
        try:
            with open(os.path.join(repo, rel), "r", errors="ignore") as fh:
                dirty += sum(1 for _ in fh)  # untracked files are unstaged too
        except OSError:
            pass
    staged = added_lines("--cached")  # staged: index vs HEAD
    total = dirty + staged

    where = "your task/scratch repo " + repo if is_task_repo(repo) else repo
    if total >= TOTAL_CAP:
        deny(
            f"SolveIt: {total} lines uncommitted in {where} (staged {staged} + "
            f"dirty {dirty}) — the {TOTAL_CAP}-line total cap is reached. Staging "
            f"won't help now; the human must commit before more is written. Tell "
            f"them what changed and why, then stop. You never commit."
        )

    if dirty >= DIRTY_CAP:
        deny(
            f"SolveIt: {dirty} unstaged lines in {where} (cap {DIRTY_CAP}; staged "
            f"lines don't count). Checkpoint due — tell the human what changed and "
            f"why, then stop. They stage what they accept (then work continues) or "
            f"commit. You never commit."
        )

    if total >= WARN_CAP:
        warn(
            f"SolveIt: {total} lines uncommitted in {where} (warn at {WARN_CAP}, "
            f"hard commit at {TOTAL_CAP}). Wrap up the current atomic step and "
            f"commit soon — keep the commit to one clear goal."
        )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open
