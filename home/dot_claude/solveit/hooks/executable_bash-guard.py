#!/usr/bin/env python3
"""SolveIt PreToolUse guard for Bash.

Bash is reserved for running task scripts and for read-only search/inspection.
A command is allowed only if every segment is one of:
  - running a task script: an interpreter (python, sh, ruby, ...) whose first
    non-flag argument is a file under .solve/tasks/<X>/ that EXISTS, in a
    folder <X> that also contains a .md; a direct ./path execution of such a
    file; or any non-destructive runner (bin/rails runner, bundle exec ruby,
    npx tsx, rake, ...) that has such a task-script file among its arguments.
    The script path must be the LAST token — no args/flags/redirects may be
    passed at run time, so a script can't be a generic command forwarder;
  - read-only search/inspection: grep, rg, find, ls, cat, head, awk, ... — the
    shell stand-ins for the Read/Grep/Glob tools, which a tool-registration bug
    can drop entirely (issue #52121), leaving the agent no other way to look at
    code. No output redirection (>, >>); `find` may not -exec/-delete. May be
    wrapped in read-only shell structure (for/while/if loops over the above).
    Each such command is appended to reads.log so the human sees what was read;
  - read-only git inspection: git diff/status/log/show/blame/ls-files/... — for
    looking at changes; no output redirection; also appended to reads.log;
  - `git init` of a task folder — to make it its own scratch repo; commits NOTHING;
  - `cd <path>` (navigation); `mv` within .solve/tasks/ (renaming the folder).
The agent NEVER commits — not the main repo, not its own task folders; the
human commits everything, leaving the tree DIRTY for review. Anything else is
blocked: ad-hoc mutating commands, test runners, installs, and git that writes
other than init (add/commit/--amend/checkout/reset/...). Fails open on any error.
"""
import datetime
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

INTERPRETERS = {
    "python", "python3", "python2", "sh", "bash", "zsh", "fish", "ruby",
    "node", "deno", "bun", "perl", "php", "Rscript", "ts-node", "tsx", "pwsh",
}
# Read-only search/inspection commands — the shell stand-ins for Read/Grep/Glob.
# Allowed because the actual tools can vanish (issue #52121); logged to reads.log.
READONLY = {
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "find", "fd",
    "ls", "cat", "bat", "head", "tail", "less", "more", "nl", "wc",
    "tree", "stat", "file", "du", "diff", "sort", "uniq", "cut", "column",
    "basename", "dirname", "realpath", "readlink", "which", "type", "pwd", "echo",
    "awk",
    # read-only helpers commonly used inside loops/conditionals:
    "printf", "test", "[", "[[", "read", "seq", "true", "false", "tr", ":",
    "comm", "join", "paste", "xxd", "od", "tac", "rev", "fold", "expand",
}
# Shell control structure — keywords that wrap commands but run nothing by
# themselves. A read-only `for/while/if ...; do <cmd>; done` is allowed: these
# keywords are peeled off and the real commands inside are validated normally.
STRUCT_PREFIX = {"do", "then", "else", "elif", "while", "until", "if", "!", "time", "{", "("}
STRUCT_ALONE = {"done", "fi", "esac", "}", ")", ";;"}
LOOP_HEADS = {"for", "select", "case"}
# `find` actions that execute or mutate — not search; route through a task script.
FIND_DANGEROUS = {
    "-exec", "-execdir", "-delete", "-ok", "-okdir",
    "-fprint", "-fprintf", "-fls",
}
# Destructive heads that may NOT borrow the "running a task script" allowance just
# because a task-folder path is among their arguments (e.g. `rm .claude/tasks/x/01.py`).
DESTRUCTIVE = {
    "rm", "rmdir", "cp", "dd", "shred", "truncate", "ln", "chmod", "chown",
    "chgrp", "mkdir", "touch", "tee", "install", "rsync", "scp", "mkfs", "sed",
}
# Flags that run an inline code/command STRING (ruby -e, python -c, sh -c,
# node --eval, ...). A runner must point at a task-script FILE, never carry inline
# code, so these are rejected on any non-read-only runner. (Read-only commands like
# `grep -e` / `head -c` are matched earlier and never reach this check.)
EVAL_FLAGS = {"-e", "-c"}
EVAL_FLAG_PREFIXES = ("--eval", "--command", "--exec", "-e=", "-c=")
REDIRECTS = {">", ">>", "1>", "2>", "&>", ">|", "2>>", "1>>"}
GIT_VALUE_OPTS = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace",
    "--exec-path", "--super-prefix",
}
# Read-only git subcommands — inspect history/working tree without mutating it.
# Allowed for looking at changes (logged to reads.log). Dual-use subcommands that
# can mutate with flags (branch, tag, remote, stash, checkout, reset, ...) are
# deliberately left out — the human owns repo mutations.
GIT_READONLY = {
    "diff", "status", "log", "show", "blame", "grep", "shortlog", "reflog",
    "rev-parse", "rev-list", "ls-files", "ls-tree", "cat-file", "describe",
    "diff-tree", "diff-index", "diff-files", "whatchanged", "show-branch",
    "name-rev", "count-objects",
}

COMMIT_MSG = (
    "SolveIt: you never commit — not the main repo, not your task/scratch folders, "
    "not anything. The whole point is to leave changes DIRTY so the human verifies "
    "and commits them. Tell the human what changed and why, then stop. The human "
    "runs every commit and --amend."
)
GENERIC_MSG = (
    "SolveIt: Bash runs task scripts and read-only search/inspection only. To RUN "
    "something, write it as a script under .solve/tasks/<folder>/ (with a .md "
    "describing it), then run it as e.g. `python .solve/tasks/<folder>/01-name.py`. "
    "To LOOK at code, use read-only commands (grep, rg, find, ls, cat, head, awk, "
    "loops over them, ...) or the Read/Grep/Glob tools. You never commit anything — "
    "leave changes dirty for the human."
)
REDIR_MSG = (
    "SolveIt: a read-only search command may not redirect output to a file (>, >>). "
    "Searching is for looking, not producing artifacts — write files with the "
    "Edit/Write tool, or run a task script under .solve/tasks/<folder>/."
)
FIND_MSG = (
    "SolveIt: `find` is allowed for search only — not -exec/-execdir/-delete/-ok. "
    "Run anything that executes or mutates as a task script under .solve/tasks/<folder>/."
)
ARGS_MSG = (
    "SolveIt: don't pass arguments (or redirects) to a task script at run time — the "
    "script path must be the last thing on the line. Passing args turns a reviewable "
    "script into a generic command forwarder (e.g. a script that runs `bin/rails \"$@\"`), "
    "which is exactly the escape hatch task scripts exist to close. Bake the exact "
    "command into the script file (the human reviews it there), then run it bare."
)
NOCODE_MSG = (
    "SolveIt: a runner may only point at a task-script FILE — it may not run an inline "
    "code string (`-e`/`-c`/`-p`/`--eval`/...). e.g. `bin/rails runner .solve/tasks/<f>/"
    "01-foo.rb` is fine; `bin/rails runner -e \"...\"` is not. Put the code in a file under "
    ".solve/tasks/<folder>/ (where the human reviews it) and run that file."
)
GIT_MSG = (
    "SolveIt: that git subcommand isn't allowed. You may only use git to LOOK — "
    "`git diff`/`status`/`log`/`show`/`blame`/`ls-files`/`rev-parse`/... (read-only, logged) — "
    "plus `git init` for a task folder. You never stage, commit, or mutate the repo (add/"
    "commit/--amend/checkout/reset/stash/apply/...): leave changes DIRTY so the human verifies "
    "and commits. Run anything that must mutate as a task script under .solve/tasks/<folder>/."
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


def git_target_dir(tokens, cwd):
    """The directory a git invocation acts on: the value of -C, else cwd."""
    k = 1
    while k < len(tokens):
        t = tokens[k]
        if t == "-C" and k + 1 < len(tokens):
            return tokens[k + 1]
        if t in GIT_VALUE_OPTS:
            k += 2
            continue
        if t.startswith("-"):
            k += 1
            continue
        break
    return cwd


def under_tasks(pathstr, cwd):
    """True if the path resolves to a child of some .solve/tasks/ folder."""
    p = pathstr if os.path.isabs(pathstr) else os.path.normpath(os.path.join(cwd, pathstr))
    parts = p.split(os.sep)
    if ".solve" not in parts:
        return False
    i = parts.index(".solve")
    return i + 2 < len(parts) and parts[i + 1] == "tasks"


def task_script_ok(pathstr, cwd):
    """A script path is runnable iff it exists under .solve/tasks/<X>/ and
    that <X> folder contains at least one .md."""
    p = pathstr if os.path.isabs(pathstr) else os.path.normpath(os.path.join(cwd, pathstr))
    parts = p.split(os.sep)
    if ".solve" not in parts:
        return (False, GENERIC_MSG)
    i = parts.index(".solve")
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


def has_inline_code_flag(toks):
    """True if any token is an inline-code/command flag (ruby -e, python -c,
    node --eval, sh -c, ...) — a runner must point at a FILE, not carry code."""
    for t in toks:
        if t in EVAL_FLAGS or t.startswith(EVAL_FLAG_PREFIXES):
            return True
    return False


def redirects_to_file(toks):
    """True if a redirect writes a real file. Redirects to /dev/null (discard)
    and fd-dups like 2>&1 (>& is not in REDIRECTS) write no file and are fine."""
    for i, t in enumerate(toks):
        if t in REDIRECTS and (i + 1 >= len(toks) or toks[i + 1] != "/dev/null"):
            return True
    return False


def segment_ok(toks, cwd):
    """Return (allowed, deny_msg, is_search) for one already-tokenized command
    segment. is_search marks a read-only search/inspection command, which the
    caller appends to reads.log."""
    j = 0
    while j < len(toks) and "=" in toks[j] and not toks[j].startswith("-"):
        j += 1
    toks = toks[j:]
    # Peel leading shell-structure keywords (`do`, `then`, `while`, `if`, ...);
    # what remains is the real command and is validated below. A `for/case/select`
    # header or a bare terminator (`done`, `fi`, ...) runs nothing → allow.
    while toks and toks[0] in STRUCT_PREFIX:
        toks = toks[1:]
    if not toks:
        return (True, None, False)
    if toks[0] in STRUCT_ALONE or toks[0] in LOOP_HEADS:
        return (True, None, False)
    head = toks[0]
    base = os.path.basename(head)

    if head == "cd":
        return (True, None, False)
    if head == "mv":  # rename/move only within .claude/tasks/ (e.g. the solve folder)
        args = [t for t in toks[1:] if not t.startswith("-")]
        if args and all(under_tasks(a, cwd) for a in args):
            return (True, None, False)
        return (False, "SolveIt: `mv` is only allowed to rename within .solve/tasks/ (e.g. a task folder).", False)
    if base == "git":
        sub = git_subcommand(toks)
        if sub == "init":  # optionally make a task folder its own scratch repo;
            return (True, None, False)  # `init` commits NOTHING
        if sub in GIT_READONLY:  # inspect the repo (diff/status/log/...) — logged, never mutates
            if redirects_to_file(toks):
                return (False, REDIR_MSG, False)
            return (True, None, True)
        # Everything else is a mutation. The agent never commits or stages —
        # anything, anywhere — so the human always reviews a dirty tree.
        if sub in ("commit", "merge", "rebase", "cherry-pick", "revert"):
            return (False, COMMIT_MSG, False)
        return (False, GIT_MSG, False)
    if base in READONLY:  # read-only search/inspection — the Read/Grep/Glob stand-ins
        if redirects_to_file(toks):
            return (False, REDIR_MSG, False)
        if base == "find" and any(t in FIND_DANGEROUS for t in toks):
            return (False, FIND_MSG, False)
        return (True, None, True)
    # Past the read-only branches, anything that runs must point at a task-script
    # FILE — never carry an inline code/command string (ruby -e, python -c, sh -c,
    # rails runner -e "...", ...). Reject those outright.
    if has_inline_code_flag(toks):
        return (False, NOCODE_MSG, False)
    if base in INTERPRETERS:
        script = next((t for t in toks[1:] if not t.startswith("-")), None)
        if script is None:
            return (False, GENERIC_MSG, False)
        ok, msg = task_script_ok(script, cwd)
        if ok and toks.index(script) != len(toks) - 1:  # args after the script
            return (False, ARGS_MSG, False)
        return (ok, msg, False)
    # Any other runner (bin/rails runner, bundle exec ruby, npx tsx, rake, ...) is
    # fine when it is running a real task-script FILE — the file under .claude/tasks/
    # is the reviewable artifact; the runner around it is incidental. Destructive
    # heads can't use this path.
    if base not in DESTRUCTIVE:
        task_arg = next(
            (t for t in toks[1:] if not t.startswith("-") and under_tasks(t, cwd)),
            None,
        )
        if task_arg is not None:
            ok, msg = task_script_ok(task_arg, cwd)
            if ok and toks.index(task_arg) != len(toks) - 1:  # args after the script
                return (False, ARGS_MSG, False)
            return (ok, msg, False)
    if "/" in head:  # direct execution of a path, e.g. ./.claude/tasks/x/run.sh
        ok, msg = task_script_ok(head, cwd)
        if ok and len(toks) > 1:  # args after the script path
            return (False, ARGS_MSG, False)
        return (ok, msg, False)
    return (False, GENERIC_MSG, False)


def repo_root(cwd):
    r = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else cwd


def allow_patterns(cwd):
    """Bash(...) globs from permissions.allow (global + project settings) — the human allowlist."""
    pats = []
    for fp in (
        os.path.expanduser("~/.claude/settings.json"),
        os.path.join(repo_root(cwd), ".claude", "settings.json"),
        os.path.join(repo_root(cwd), ".claude", "settings.local.json"),
    ):
        try:
            allow = json.load(open(fp)).get("permissions", {}).get("allow", [])
        except (OSError, ValueError, AttributeError):
            continue
        pats += [e[5:-1] for e in allow if isinstance(e, str) and e.startswith("Bash(") and e.endswith(")")]
    return pats


def solve_dir(cwd):
    """<repo-root>/.solve — where reads.log lives (git-excluded)."""
    return os.path.join(repo_root(cwd), ".solve")


def log_search(cmd, cwd):
    """Append a read-only Bash search to <repo>/.solve/reads.log (mirrors
    log-reads.py) so the human sees shell searches alongside Read/Grep/Glob.
    Never blocks the command."""
    try:
        d = solve_dir(cwd)
        os.makedirs(d, exist_ok=True)
        ts = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        with open(os.path.join(d, "reads.log"), "a") as f:
            f.write(f"{ts}\tBash\t{cmd.strip()}\n")
    except OSError:
        pass


CONTROL_OPS = {"|", "||", "&&", ";", ";;", "&", "|&"}


def split_segments(cmd):
    """Split a command line into quote-aware command segments (lists of tokens).

    Splits on the shell control operators in CONTROL_OPS, but NOT on operator
    characters that sit inside quotes or are escaped — so `grep "a\\|b"` and a
    commit message containing `;` stay in one segment. Tokenizing per line keeps
    newline a separator (shlex treats it as plain whitespace). Falls back to the
    naive regex split for any line shlex can't parse (e.g. unbalanced quotes)."""
    segs = []
    for line in cmd.split("\n"):
        try:
            lex = shlex.shlex(line, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            toks = list(lex)
        except ValueError:
            for piece in re.split(r"&&|\|\||;|\|", line):
                try:
                    segs.append(shlex.split(piece))
                except ValueError:
                    segs.append(piece.split())
            continue
        cur = []
        for t in toks:
            if t in CONTROL_OPS:
                segs.append(cur)
                cur = []
            else:
                cur.append(t)
        segs.append(cur)
    return segs


def main():
    if os.environ.get("SOLVEIT_OFF"):
        return
    data = json.load(sys.stdin)
    cmd = (data.get("tool_input") or {}).get("command", "")
    cwd = data.get("cwd") or os.getcwd()
    if not cmd:
        return
    patterns = allow_patterns(cwd)
    is_search = False
    for toks in split_segments(cmd):
        ok, msg, search = segment_ok(toks, cwd)
        if not ok:
            seg = " ".join(toks).strip()
            if seg and any(fnmatch.fnmatchcase(seg, p) for p in patterns):
                ok, search = True, False
        if not ok:
            sys.stderr.write(msg)
            sys.exit(2)
        is_search = is_search or search
    if is_search:  # log the whole command once, like a Grep/Glob entry
        log_search(cmd, cwd)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open
