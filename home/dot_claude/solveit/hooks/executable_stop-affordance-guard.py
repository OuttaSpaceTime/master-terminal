#!/usr/bin/env python3
"""SolveIt Stop hook: turn-level rules, checked once the turn ends.

Blocks a trailing menu, asking the human to paste output, prose past
BLOCK_CHARS when they did not ask for depth, an unhedged confident claim on a
turn where nothing ran (the human's `!` run whose output started the turn
counts as a run), a task script written but neither run nor shown, and any
command the human would copy that spans more than one line (pasting a
multi-line command mangles newlines).

The turn's final assistant message is flushed to the transcript a moment AFTER
the Stop hook fires, so a single read can miss it. We poll the transcript
briefly (STOP_GUARD_POLL tries, spaced by STOP_GUARD_POLL_INTERVAL seconds)
until that closing text has landed.

Fails open: never blocks when SOLVEIT_OFF is set, when already re-triggered
this turn (stop_hook_active), or on any read/parse error.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solve_allow import log_guard_error

AFFORDANCE = "▶"

# Fenced-block languages that are commands the human copies and runs (not code
# to read). A block tagged with one of these must be a SINGLE command line.
SHELL_LANGS = {"bash", "sh", "shell", "zsh", "fish"}
_FENCE = re.compile(r"^```([^`]*)$")

MENU = re.compile(
    r"(?i)(want me to|should i|shall i|next step|i can (also|now)|if you want,? i)[^?]*\?\s*$"
)
PASTE_BACK = re.compile(
    r"(?i)(paste (the|it|that|your|them)|tell me what you (see|get)|let me know what|"
    r"report back|then i'?ll (write|decide|continue|take))"
)
DEPTH = re.compile(r"(?i)\b(explain|detail|walk me through|elaborate|in depth|deeper)\b")
CONFIDENT = re.compile(
    r"(?i)\b(confirmed|definitely|certainly|clearly|proves|now i (fully )?understand)\b"
)
HEDGE = re.compile(r"(?i)(looks like|i think|probably|seems|hypothes|my guess|likely|not sure)")
RUNNERS = {"Bash", "BashOutput"}
WRITERS = {"Write", "Edit", "MultiEdit"}
WARN_CHARS, BLOCK_CHARS = 1200, 2200

_FENCE_BLOCK = re.compile(r"```.*?```", re.S)
TASK_SCRIPT = re.compile(r"(^|/)\.solve/tasks/[^/]+/.+")


MENU_MSG = (
    "SolveIt: you ended with a menu. The human sets direction — if the step is "
    "reversible and their taste doesn't decide it, take it and let current.<ext> "
    "show it. If it genuinely needs their call, ask ONE question, not a choice "
    "between your plans.\n"
)
PASTE_MSG = (
    "SolveIt: don't ask the human to paste output or report back. When they run "
    "current.<ext> with `!`, its output lands in the transcript — read it there.\n"
)
HEDGE_MSG = (
    "SolveIt: this turn only read — nothing ran — yet it asserts. A claim drawn from "
    "reading is a hypothesis: say 'looks like' / 'I think', or prove it — write "
    "current.<ext> so it prints the real value behind the claim, and give the human "
    "its one-line `!` run command.\n"
)
SCRIPT_MSG = (
    "SolveIt: you wrote {name} but this turn neither ran it nor shows it. Run it "
    "now and report what it printed — or, if it is not ready to run, say in one "
    "line what it does and show it fenced.\n"
)
LENGTH_MSG = (
    "SolveIt: {n} characters of prose since the human's last message, and they did "
    "not ask for depth. Brevity is rule #1 — give the answer, and leave the detail "
    "to current.<ext> and its output.\n"
)


REPAIR = (
    "The text you already wrote is on the human's screen and stays there — do not "
    "write it again in other words. Send only the correction, plus one sentence if "
    "it needs a lead-in.\n"
)


LENGTH_REPAIR = (
    "They have already read it — don't send a shortened rewrite of the same answer. "
    "Say nothing further, and keep the next turn to the answer plus what "
    "current.<ext> printed.\n"
)


def die(msg, repair=REPAIR):
    sys.stderr.write(msg + repair)
    sys.exit(2)


def _final_paragraph(body):
    return body.rsplit("\n\n", 1)[-1].strip()


def _prose(span):
    """The span minus fenced blocks — a draft, diff or script the human asked for
    is payload, not prose."""
    return _FENCE_BLOCK.sub("", span).strip()


MULTILINE_MSG = (
    "SolveIt: a runnable command in your response spans multiple lines. The human "
    "copies commands straight out of the chat, and pasting a multi-line command "
    "mangles newlines — every command they run must fit on ONE line. Join steps with "
    "'&&' or ';' onto a single line, or if it genuinely can't be one line, put it in "
    "current.<ext> and give the one-line run command (e.g. "
    "'python .solve/tasks/<f>/current.py'). No backslash line-continuations, "
    "no multi-line bash/sh/zsh fenced blocks.\n"
)


def _has_multiline_command(text):
    """True if the response contains a command the human would copy that is not
    on a single line: a ▶ line continued with a trailing backslash, or a
    shell-tagged fenced block with more than one command line. A block whose
    first line is a comment is a script listing (the task-script convention puts
    the run command there), not something the human pastes."""
    in_shell_fence = False
    fenced = []
    for line in text.split("\n"):
        stripped = line.strip()
        fence = _FENCE.match(stripped)
        if fence:
            if in_shell_fence:
                listing = fenced and fenced[0].startswith("#")
                if not listing and len([l for l in fenced if not l.startswith("#")]) > 1:
                    return True
                in_shell_fence = False
            elif fence.group(1).strip().lower() in SHELL_LANGS:
                in_shell_fence = True
            fenced = []
            continue
        if in_shell_fence and stripped:
            fenced.append(stripped)
        if AFFORDANCE in line and line.rstrip().endswith("\\"):
            return True
    return False


def _is_tool_result(content):
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content
    )


def _user_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def _assistant_text_since_last_user(entries):
    """(assistant text since the human's last message, that message's text,
    whether anything ran, task scripts written)."""
    start, last_user = 0, ""
    for i in range(len(entries) - 1, -1, -1):
        e = entries[i]
        if e.get("type") != "user":
            continue
        content = (e.get("message") or {}).get("content")
        if _is_tool_result(content):
            continue
        start, last_user = i + 1, _user_text(content)
        break
    texts, ran, scripts = [], last_user.startswith("<bash-stdout>"), []
    for e in entries[start:]:
        content = (e.get("message") or {}).get("content")
        if not isinstance(content, list) or e.get("type") != "assistant":
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                texts.append(b.get("text", ""))
            elif b.get("type") == "tool_use" and b.get("name") in RUNNERS:
                ran = True
            elif b.get("type") == "tool_use" and b.get("name") in WRITERS:
                fp = (b.get("input") or {}).get("file_path") or ""
                if TASK_SCRIPT.search(fp):
                    scripts.append(fp[fp.index(".solve/"):])
    return "\n".join(texts), last_user, ran, scripts


def _read_entries(path):
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def _final_text_flushed(entries):
    """True once the turn's closing message is in the transcript: the last
    user/assistant entry is assistant text, not the prompt, a tool call or a
    tool result."""
    for e in reversed(entries):
        if e.get("type") == "user":
            return False
        if e.get("type") == "assistant":
            content = (e.get("message") or {}).get("content")
            return isinstance(content, list) and any(
                isinstance(b, dict) and b.get("type") == "text" for b in content
            )
    return False


def main():
    if os.environ.get("SOLVEIT_OFF"):
        return
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    tries = int(os.environ.get("STOP_GUARD_POLL", "8"))
    interval = float(os.environ.get("STOP_GUARD_POLL_INTERVAL", "0.25"))
    entries = _read_entries(path)
    for _ in range(tries):
        if _final_text_flushed(entries):
            break
        time.sleep(interval)
        entries = _read_entries(path)
    span, last_user, ran, scripts = _assistant_text_since_last_user(entries)
    body = _prose(span)
    for fp in scripts if not ran else []:
        name = os.path.basename(fp)
        if name not in span or not _FENCE_BLOCK.search(span):
            die(SCRIPT_MSG.format(name=name))
    if MENU.search(_final_paragraph(body)):
        die(MENU_MSG)
    if PASTE_BACK.search(body):
        die(PASTE_MSG)
    if len(body) > BLOCK_CHARS and not DEPTH.search(last_user):
        die(LENGTH_MSG.format(n=len(body)), LENGTH_REPAIR)
    if _has_multiline_command(span):
        die(MULTILINE_MSG)
    if not ran and CONFIDENT.search(body) and not HEDGE.search(body):
        die(HEDGE_MSG)


def run_guarded():
    """Fail open on any internal error — but leave a trace, since a silent crash
    here means the turn went out unchecked."""
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        log_guard_error("stop-affordance-guard")
    sys.exit(0)


if __name__ == "__main__":
    run_guarded()
