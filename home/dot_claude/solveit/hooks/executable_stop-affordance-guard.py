#!/usr/bin/env python3
"""SolveIt Stop hook: require a probe/verify affordance in the response.

No PreToolUse guard fires on a turn that only reads/searches, so a pure
research/tracing answer can narrate confident, unverified synthesis with
nothing to block it. This Stop hook closes that gap: it reads the transcript,
takes the assistant text produced since the last genuine user message, and if
it contains no affordance marker (the "▶" cue that leads every probe/verify
handoff) it blocks (exit 2) so the model must ground the answer with one.

It also enforces that any command the human copies out of the chat fits on ONE
line: once the affordance is present, a ▶ line continued with a trailing
backslash or a multi-line bash/sh/zsh fenced block blocks too, since pasting a
multi-line command mangles newlines.

The turn's final assistant message is flushed to the transcript a moment AFTER
the Stop hook fires, so a single read sees an empty/stale span and would block
every turn. We poll the transcript briefly (STOP_GUARD_POLL tries, spaced by
STOP_GUARD_POLL_INTERVAL seconds) until the affordance appears, and only block
if it never does.

Fails open: never blocks when SOLVEIT_OFF is set, when already re-triggered
this turn (stop_hook_active), or on any read/parse error.
"""
import json
import os
import re
import sys
import time

AFFORDANCE = "▶"

# Fenced-block languages that are commands the human copies and runs (not code
# to read). A block tagged with one of these must be a SINGLE command line.
SHELL_LANGS = {"bash", "sh", "shell", "zsh", "fish"}
_FENCE = re.compile(r"^```([^`]*)$")

MULTILINE_MSG = (
    "SolveIt: a runnable command in your response spans multiple lines. The human "
    "copies commands straight out of the chat, and pasting a multi-line command "
    "mangles newlines — every command they run must fit on ONE line. Join steps with "
    "'&&' or ';' onto a single line, or if it genuinely can't be one line, write it as "
    "a task script and hand the human the one-line run command (e.g. "
    "'▶ Verify: python .solve/tasks/<f>/01-name.py'). No backslash line-continuations, "
    "no multi-line bash/sh/zsh fenced blocks.\n"
)


def _has_multiline_command(text):
    """True if the response contains a command the human would copy that is not
    on a single line: a ▶ affordance line continued with a trailing backslash, or
    a shell-tagged fenced block with more than one command line."""
    in_shell_fence = False
    cmd_lines = 0
    for line in text.split("\n"):
        stripped = line.strip()
        fence = _FENCE.match(stripped)
        if fence:
            if in_shell_fence:
                if cmd_lines > 1:
                    return True
                in_shell_fence = False
                cmd_lines = 0
            elif fence.group(1).strip().lower() in SHELL_LANGS:
                in_shell_fence = True
                cmd_lines = 0
            continue
        if in_shell_fence and stripped and not stripped.startswith("#"):
            cmd_lines += 1
        if AFFORDANCE in line and line.rstrip().endswith("\\"):
            return True
    return False


def _is_tool_result(content):
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content
    )


def _assistant_text_since_last_user(entries):
    start = 0
    for i in range(len(entries) - 1, -1, -1):
        e = entries[i]
        if e.get("type") != "user":
            continue
        if _is_tool_result((e.get("message") or {}).get("content")):
            continue
        start = i + 1
        break
    texts = []
    for e in entries[start:]:
        if e.get("type") != "assistant":
            continue
        content = (e.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                texts.append(b.get("text", ""))
    return "\n".join(texts)


def _read_span(path):
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return _assistant_text_since_last_user(entries)


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
    span = _read_span(path)
    for _ in range(tries):
        if AFFORDANCE in span:
            break
        time.sleep(interval)
        span = _read_span(path)
    if AFFORDANCE in span:
        if _has_multiline_command(span):
            sys.stderr.write(MULTILINE_MSG)
            sys.exit(2)
        return
    sys.stderr.write(
        "SolveIt: your response since the last user message has no probe/verify "
        "affordance (▶). A claim drawn from reading is a hypothesis, not an "
        "answer. Hand the human ONE runnable or readable probe and ask them to "
        "predict first — e.g. '▶ Predict, then run: <cmd>', "
        "'▶ Verify: <cmd>', '▶ run <test>', or "
        "'▶ nvim +<line> <path>'. Add one, or state plainly why a direct "
        "answer was requested.\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)
