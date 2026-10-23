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
     Escape valve for a deliberate multi-commit split — one pile built on purpose,
     then sliced into several commits: the human runs `touch .solve/splitting` in
     the session's cwd. That lifts CAP and all three tiers above, but never
     EDIT_CAP (the hand-back rhythm stays) and never CAP for a write inside
     .solve/tasks/. The first project write
     stamps its session_id into the file; a later session finds a foreign id,
     deletes it and enforces the caps again — so the valve is off by default and
     dies with the chat. Writes to the marker itself are denied: the human drops
     it, never the agent.
     .solve/ is git-excluded, so task-folder scripts never inflate the main
     repo's count — it tracks real project changes. A write inside .solve/tasks/
     skips the three tiers: every step archives its current.<ext> there, so
     scratch grows by design and only CAP bounds a write. Each .solve/tasks/<X>
     folder is auto-git-init'd on first write so the human can commit its history.
     Either way the agent never commits — it stops and the human commits.
  3. a write creates a NEW current.<ext> (the path doesn't exist: archived away,
     or another extension) while the current.<ext> Claude wrote before the human's
     last prompt hasn't been run yet. Project writes and in-place fixes of the
     unrun script still land. Only the human runs current.<ext>, with
     `! <command>` (bash-guard refuses Claude's runs), and the next script
     waits for that output. The turn the human's `!` output starts only reads
     it: no project write until their next message. Read from the transcript; a
     write a guard denied doesn't count.
  4. a write would create a SECOND .solve/tasks/<X> folder in one session. The
     first task folder written to is recorded per session_id (state file
     ~/.claude/solveit/state/<session>.taskdir); later writes must target that
     same folder — add more scripts there rather than opening a new folder.

30 lines is a hard ceiling per step, not a target. Fails open: any internal
error allows the tool call so a bug here never wedges a session.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solve_allow import log_guard_error

CAP = 30  # per single edit/write
EDIT_CAP = 1  # project-code edits per human turn (reset by solve-init on each prompt)
DIRTY_CAP = 30  # unstaged + untracked -> pause & force stage
WARN_CAP = 150  # staged + unstaged + untracked -> warn, proceed
TOTAL_CAP = 300  # staged + unstaged + untracked -> hard block, force commit
CURRENT = re.compile(r"\.solve/tasks/[^/\s]+/current\.\w+")
NOT_RUNS = {"cat", "head", "tail", "less", "bat", "nvim", "vim", "view", "mv", "cp", "ls",
            "wc", "grep", "rg", "sed", "awk"}


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


def task_folder_root(fp):
    """The .solve/tasks/<X> folder a path lives under, or None."""
    parts = fp.split(os.sep)
    if ".solve" not in parts:
        return None
    i = parts.index(".solve")
    if i + 2 < len(parts) and parts[i + 1] == "tasks":
        return os.sep.join(parts[: i + 3])
    return None


def runs_current(command):
    """True when a segment of the command ends in current.<ext> and is not a read
    or the archiving mv."""
    for segment in re.split(r"&&|\|\||[;|]", command):
        toks = segment.split()
        if toks and CURRENT.search(toks[-1]) and toks[0] not in NOT_RUNS:
            return True
    return False


def unrun_current(transcript):
    """(the current.<ext> Claude wrote before the human's last prompt that the
    human has not run with `!` since, or None; whether a `!` started this turn)."""
    written, last_write, held, bang = {}, None, None, False
    with open(transcript) as f:
        for line in f:
            e = json.loads(line)
            content = (e.get("message") or {}).get("content")
            if e.get("type") == "assistant" and isinstance(content, list):
                for b in content:
                    fp = (b.get("input") or {}).get("file_path") or ""
                    if b.get("type") == "tool_use" and CURRENT.search(fp):
                        written[b.get("id")] = CURRENT.search(fp).group()
            elif e.get("type") == "user" and isinstance(content, list):
                for b in content:
                    if b.get("type") == "tool_result" and not b.get("is_error"):
                        last_write = written.get(b.get("tool_use_id"), last_write)
            elif e.get("type") == "user" and isinstance(content, str):
                bang = content.startswith("<bash-")
                ran = re.match(r"<bash-input>(.*)</bash-input>", content, re.S)
                if ran and runs_current(ran.group(1)):
                    last_write = held = None
                elif not content.startswith("<bash-"):
                    held = last_write
    return held, bang


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

    if fp.endswith(os.path.join(".solve", "splitting")):
        deny(
            "SolveIt: .solve/splitting is the human's escape valve — they drop it "
            "with `touch .solve/splitting`, never you."
        )

    session = data.get("session_id") or "nosession"
    splitting = False
    valve = os.path.join(cwd, ".solve", "splitting")
    if os.path.exists(valve) and not task_folder_root(fp):
        owner = open(valve).read().strip()
        if not owner:
            open(valve, "w").write(session + "\n")
        if not owner or owner == session:
            splitting = True
        else:
            os.remove(valve)

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
    if added > CAP and not splitting:
        deny(
            f"SolveIt: this step adds {added} lines (hard ceiling {CAP}). "
            f"That ceiling is not a target — make a genuinely small change, "
            f"one idea at a time, and hand it back to verify."
        )

    # Make each .solve/tasks/<X> folder its own scratch repo so the human can
    # commit its history; the agent never does.
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
    transcript = data.get("transcript_path")
    if transcript and os.path.exists(transcript):
        held, bang = unrun_current(transcript)
        if bang:
            deny(
                "SolveIt: the human's `!` output started this turn. Quote the lines "
                "that matter, name the next step and stop — nothing is written until "
                "their next message."
            )
        if held and CURRENT.search(fp) and not os.path.exists(fp):
            deny(
                f"SolveIt: the human hasn't run {held} since you wrote it, so the next "
                f"current.<ext> waits. Fix it in place if needed (move it back if you "
                f"archived it), give them its one-line run command prefixed with `! ` "
                f"and stop."
            )
    if not task_root:
        session = data.get("session_id") or "nosession"
        counter = os.path.expanduser(f"~/.claude/solveit/state/{session}.edits")
        n = (int(open(counter).read().strip() or 0) if os.path.exists(counter) else 0) + 1
        os.makedirs(os.path.dirname(counter), exist_ok=True)
        open(counter, "w").write(f"{n}\n")
        if n > EDIT_CAP:
            deny(
                f"SolveIt: {n} edits to project code since the human's last message "
                f"(cap {EDIT_CAP}). One step lands per turn — hand back now so they "
                f"inspect this one in the diff and in current.<ext> first."
            )
    if task_root and not os.path.isdir(os.path.join(task_root, ".git")):
        os.makedirs(task_root, exist_ok=True)
        git(task_root, "init", "-q")
    if task_root:
        return

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

    if splitting:
        return

    if total >= TOTAL_CAP:
        deny(
            f"SolveIt: {total} lines uncommitted in {repo} (staged {staged} + "
            f"dirty {dirty}) — the {TOTAL_CAP}-line total cap is reached. Staging "
            f"won't help now; the human must commit before more is written. Tell "
            f"them what changed and why, then stop. You never commit."
        )

    if dirty >= DIRTY_CAP:
        deny(
            f"SolveIt: {dirty} unstaged lines in {repo} (cap {DIRTY_CAP}; staged "
            f"lines don't count). Checkpoint due — tell the human what changed and "
            f"why, then stop. They stage what they accept (then work continues) or "
            f"commit. You never commit."
        )

    if total >= WARN_CAP:
        warn(
            f"SolveIt: {total} lines uncommitted in {repo} (warn at {WARN_CAP}, "
            f"hard commit at {TOTAL_CAP}). Wrap up the current atomic step and "
            f"commit soon — keep the commit to one clear goal."
        )


def run_guarded():
    """Fail open on any internal error — but leave a trace, since a silent crash
    here means the edit landed uncapped."""
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        log_guard_error("edit-guard")
        sys.exit(0)


if __name__ == "__main__":
    run_guarded()
