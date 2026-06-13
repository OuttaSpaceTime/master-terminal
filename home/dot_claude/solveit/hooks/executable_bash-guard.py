#!/usr/bin/env python3
"""SolveIt PreToolUse guard for Bash — strict.

Bash is reserved for running task scripts. A command is allowed only if every
segment is one of:
  - running a task script: an interpreter (python, sh, ruby, ...) whose first
    non-flag argument is a file under .claude/tasks/<X>/ that EXISTS, in a
    folder <X> that also contains a .md; or a direct ./path execution of such
    a file;
  - `git init` (so a task folder can become its own repo);
  - `cd <path>` (navigation).
Anything else is blocked: ad-hoc commands, read-only shell (use the Read/Grep/
Glob tools instead), test runners, installs, and `git commit`/`--amend` (the
human commits). Fails open on any internal error.
"""
import json
import os
import re
import shlex
import sys

INTERPRETERS = {
    "python", "python3", "python2", "sh", "bash", "zsh", "fish", "ruby",
    "node", "deno", "bun", "perl", "php", "Rscript", "ts-node", "tsx", "pwsh",
}
GIT_VALUE_OPTS = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace",
    "--exec-path", "--super-prefix",
}

COMMIT_MSG = (
    "SolveIt: you don't commit - that's the human's checkpoint. Tell the human "
    "what to commit (the main repo and/or the task folder) and why, then stop. "
    "The human runs the commit (and any --amend)."
)
GENERIC_MSG = (
    "SolveIt: Bash only runs task scripts. Write what you want to run as a "
    "script under .claude/tasks/<folder>/ (with a .md describing it), then run "
    "it as e.g. `python .claude/tasks/<folder>/01-descriptive-name.py`. Explore "
    "with your Read/Grep/Glob tools instead of shell, run one script per command "
    "(no chaining). `git init` for a task folder is allowed; you never commit."
)


def git_subcommand(tokens):
    k = 1
    while k < len(tokens):
        t = tokens[k]
        if t in GIT_VALUE_OPTS:
            k += 2
            continue
        if t.startswith("-"):
            k += 1
            continue
        return t
    return None


def under_tasks(pathstr, cwd):
    """True if the path resolves to a child of some .claude/tasks/ folder."""
    p = pathstr if os.path.isabs(pathstr) else os.path.normpath(os.path.join(cwd, pathstr))
    parts = p.split(os.sep)
    if ".claude" not in parts:
        return False
    i = parts.index(".claude")
    return i + 2 < len(parts) and parts[i + 1] == "tasks"


def task_script_ok(pathstr, cwd):
    """A script path is runnable iff it exists under .claude/tasks/<X>/ and
    that <X> folder contains at least one .md."""
    p = pathstr if os.path.isabs(pathstr) else os.path.normpath(os.path.join(cwd, pathstr))
    parts = p.split(os.sep)
    if ".claude" not in parts:
        return (False, GENERIC_MSG)
    i = parts.index(".claude")
    if not (i + 2 < len(parts) and parts[i + 1] == "tasks"):
        return (False, GENERIC_MSG)
    task_dir = os.sep.join(parts[: i + 3])
    if not os.path.isfile(p):
        return (False, f"SolveIt: the script {pathstr} does not exist yet - write it first, then run it.")
    try:
        has_md = any(f.endswith(".md") for f in os.listdir(task_dir))
    except OSError:
        has_md = False
    if not has_md:
        return (False, f"SolveIt: write a .md describing this task in {task_dir}/ before running its scripts.")
    return (True, None)


def segment_ok(seg, cwd):
    try:
        toks = shlex.split(seg)
    except ValueError:
        toks = seg.split()
    j = 0
    while j < len(toks) and "=" in toks[j] and not toks[j].startswith("-"):
        j += 1
    toks = toks[j:]
    if not toks:
        return (True, None)
    head = toks[0]

    if head == "cd":
        return (True, None)
    if head == "mv":  # rename/move only within .claude/tasks/ (e.g. the solve folder)
        args = [t for t in toks[1:] if not t.startswith("-")]
        if args and all(under_tasks(a, cwd) for a in args):
            return (True, None)
        return (False, "SolveIt: `mv` is only allowed to rename within .claude/tasks/ (e.g. the solve folder).")
    if os.path.basename(head) == "git":
        sub = git_subcommand(toks)
        if sub == "init":
            return (True, None)
        if sub == "commit":
            return (False, COMMIT_MSG)
        return (False, GENERIC_MSG)
    if os.path.basename(head) in INTERPRETERS:
        script = next((t for t in toks[1:] if not t.startswith("-")), None)
        if script is None:
            return (False, GENERIC_MSG)
        return task_script_ok(script, cwd)
    if "/" in head:  # direct execution of a path, e.g. ./.claude/tasks/x/run.sh
        return task_script_ok(head, cwd)
    return (False, GENERIC_MSG)


def main():
    data = json.load(sys.stdin)
    cmd = (data.get("tool_input") or {}).get("command", "")
    cwd = data.get("cwd") or os.getcwd()
    if not cmd:
        return
    for seg in re.split(r"&&|\|\||;|\n|\|", cmd):
        ok, msg = segment_ok(seg, cwd)
        if not ok:
            sys.stderr.write(msg)
            sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open
