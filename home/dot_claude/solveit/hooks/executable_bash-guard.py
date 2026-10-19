#!/usr/bin/env python3
"""SolveIt PreToolUse guard for Bash.

Bash is reserved for running task scripts and for read-only search/inspection.
A command is allowed only if every segment is one of:
  - running a task script: an interpreter (python, sh, ruby, ...) whose first
    non-flag argument is a file under .solve/tasks/<X>/ that EXISTS; a direct
    ./path execution of such a
    file; or any non-destructive runner (bin/rails runner, bundle exec ruby,
    npx tsx, rake, ...) that has such a task-script file among its arguments.
    The script path must be the LAST token — no args/flags/redirects may be
    passed at run time, so a script can't be a generic command forwarder. The
    one exception is current.<ext>, the step's check: only the human runs it,
    with `! <command>`, and its output lands in the transcript;
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
import json
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solve_allow import allow_patterns, log_guard_error, repo_root

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
BUNDLE_READONLY = {
    "show", "info", "list", "env", "platform", "check", "outdated",
    "doctor", "version",
}

COMMIT_MSG = "SolveIt: you never commit or amend, anywhere. Say what changed and why, then stop."
GENERIC_MSG = (
    "SolveIt: Bash runs task scripts + read-only search. Put it under .solve/tasks/<f>/ "
    "and run that file, or look with grep/rg/find/ls/cat/head/awk."
)
REDIR_MSG = "SolveIt: no > / >> from a search. Write files with Edit/Write, or run a task script."
FIND_MSG = "SolveIt: `find` searches only — no -exec/-delete. Run it as a task script instead."
ARGS_MSG = (
    "SolveIt: no args or redirects after a task script — the script path is the last "
    "token. Bake the exact command into the file, then run it bare."
)
NOCODE_MSG = (
    "SolveIt: a runner points at a task-script FILE, never inline code (-e/-c/--eval). "
    "Put it under .solve/tasks/<f>/ and run that file."
)
CURRENT_MSG = (
    "SolveIt: the human runs current.<ext>, not you. Give them its one-line run "
    "command prefixed with `!` (e.g. `! ruby .solve/tasks/<f>/current.rb`) and stop; "
    "its output lands in the transcript for you to read.\n"
)
GIT_MSG = (
    "SolveIt: git may only LOOK — diff/status/log/show/blame/ls-files/rev-parse, plus "
    "`git init` for a task folder. You never stage, commit, or mutate the repo."
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
    pathstr = os.path.expanduser(pathstr)
    p = pathstr if os.path.isabs(pathstr) else os.path.normpath(os.path.join(cwd, pathstr))
    parts = p.split(os.sep)
    if ".solve" not in parts:
        return False
    i = parts.index(".solve")
    return i + 2 < len(parts) and parts[i + 1] == "tasks"


def task_script_ok(pathstr, cwd):
    """A script path is runnable iff it exists under .solve/tasks/<X>/."""
    pathstr = os.path.expanduser(pathstr)
    p = pathstr if os.path.isabs(pathstr) else os.path.normpath(os.path.join(cwd, pathstr))
    parts = p.split(os.sep)
    if ".solve" not in parts:
        return (False, GENERIC_MSG)
    i = parts.index(".solve")
    if not (i + 2 < len(parts) and parts[i + 1] == "tasks"):
        return (False, GENERIC_MSG)
    if not os.path.isfile(p):
        return (False, f"SolveIt: the script {pathstr} does not exist yet - write it first, then run it.")
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
    if base == "bundle":
        sub = next((t for t in toks[1:] if not t.startswith("-")), None)
        if sub in BUNDLE_READONLY:
            if redirects_to_file(toks):
                return (False, REDIR_MSG, False)
            return (True, None, True)
    if base in READONLY:  # read-only search/inspection — the Read/Grep/Glob stand-ins
        if redirects_to_file(toks):
            return (False, REDIR_MSG, False)
        if base == "find" and any(t in FIND_DANGEROUS for t in toks):
            return (False, FIND_MSG, False)
        return (True, None, True)
    if under_tasks(toks[-1], cwd) and re.fullmatch(r"current\.\w+", os.path.basename(toks[-1])):
        return (False, CURRENT_MSG, False)
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


def allowlisted(seg, patterns):
    """Match a segment against Claude Code Bash(...) allow rules, mirroring its
    native matching so the hook never blocks a command the human already allowed:
    `prefix:*` is a prefix rule (the prefix plus any args); a trailing `*` is a
    glob (`chezmoi ... diff*` matches `chezmoi ... diff`, `ls*` matches `lsof`);
    no wildcard is exact. fnmatch can't express `:*` — it reads the `:` literally,
    so `bundle exec rubocop:*` never matches `bundle exec rubocop -A x`."""
    for p in patterns:
        if p.endswith(":*"):
            prefix = p[:-2]
            if seg == prefix or seg.startswith(prefix + " "):
                return True
        elif p.endswith("*"):
            if seg.startswith(p[:-1]):
                return True
        elif seg == p:
            return True
    return False


def cd_target(toks, cwd):
    """If toks is a plain `cd <dir>`, the directory it moves to — so later
    segments in the same command resolve paths against it, not the original
    cwd. `cd` alone or `cd -` aren't tracked (ambiguous without shell state)."""
    if toks[:1] != ["cd"] or len(toks) != 2:
        return None
    d = os.path.expanduser(toks[1])
    return d if os.path.isabs(d) else os.path.normpath(os.path.join(cwd, d))


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
        if not ok and msg is not CURRENT_MSG:
            seg = " ".join(toks).strip()
            if seg and allowlisted(seg, patterns):
                ok, search = True, False
        if not ok:
            sys.stderr.write(msg)
            sys.exit(2)
        is_search = is_search or search
        target = cd_target(toks, cwd)
        if target is not None:
            cwd = target
    if is_search:  # log the whole command once, like a Grep/Glob entry
        log_search(cmd, cwd)


def run_guarded():
    """Fail open on any internal error — but leave a trace, since a silent crash
    here means the command ran unguarded."""
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        log_guard_error("bash-guard")
        sys.exit(0)


if __name__ == "__main__":
    run_guarded()
