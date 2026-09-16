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
CHECKPOINT = re.compile(
    r"(?i)(unstaged lines|checkpoint|stage what you accept|before i write more|"
    r"total cap|must commit)"
)
RUNNERS = {"Bash", "BashOutput"}
WRITERS = {"Write", "Edit", "MultiEdit"}
WARN_CHARS, BLOCK_CHARS = 1200, 2200

_FENCE_BLOCK = re.compile(r"```.*?```", re.S)
ACK = re.compile(
    r"(?i)\b(applied|staged|reverted|committed|done|nice|removed|renamed|written|"
    r"wrote|fixed|updated|noted|green|passing)\b"
)
CLAIM = re.compile(
    r"(?i)\b(because|means|the (bug|cause|reason)|it (is|does|will)|confirmed|"
    r"proves|therefore|which is why)\b"
)
# A probe that only opens or searches files. It can build the model, but it never
# shows a runtime value, so it cannot be the whole verify for a behaviour claim.
READING_PROBE = re.compile(
    r"^(nvim|vim|vi|view|less|more|bat|cat|head|tail|sed|open|code|grep|rg|ag|ack)\b"
)
PROBE_LABEL = re.compile(r"^[A-Za-z][^:]{0,30}:\s*")
TASK_SCRIPT = re.compile(r"(^|/)\.solve/tasks/[^/]+/.+")


MENU_MSG = (
    "SolveIt: you ended with a menu. The human sets direction — if the step is "
    "reversible and their taste doesn't decide it, do it and hand back the verify "
    "command. If it genuinely needs their call, ask ONE question, not a choice "
    "between your plans.\n"
)
PASTE_MSG = (
    "SolveIt: don't ask the human to paste output or report back. You check the "
    "output/file/test yourself and say in one line what you saw; the probe you hand "
    "over is theirs to run for their own understanding, and nothing waits on their "
    "reply.\n"
)
VERIFY_MSG = (
    "SolveIt: '▶ Verify:' means you already ran it and are reporting what you saw — "
    "but nothing ran this turn. Either run it first and say the result in one line, or "
    "hand it over as '▶ Try: <cmd>' — theirs to run for their own understanding.\n"
)
HEDGE_MSG = (
    "SolveIt: this turn only read — nothing ran — yet it asserts. A claim drawn from "
    "reading is a hypothesis: say 'looks like' / 'I think', and make the probe "
    "something that prints a real value (a script, a test, a breakpoint) rather than "
    "another reading assignment.\n"
)
WEAK_PROBE_MSG = (
    "SolveIt: this turn claims how the code behaves, and its only probe is a reading "
    "assignment (nvim/grep). Too weak — make the code reveal itself: a "
    "`debugger`/`binding.irb`/`breakpoint()` on the exact line, then the command that "
    "hits it and the value to print once stopped; a console/REPL line on the real "
    "object (`.to_sql`, the real record); or a task script or test that prints the "
    "actual intermediate value. Ask them to predict that value first. Keep the "
    "'▶ nvim +<line>' too if reading builds the model — it just can't be the whole "
    "verify.\n"
)
SCRIPT_MSG = (
    "SolveIt: you wrote {name} but this turn neither ran it nor shows it. Either run "
    "it now and report what it printed, or — if it is not ready to run — say in one "
    "line what it does and what you expect it to print, show the script fenced, and "
    "hand over `▶ nvim {path}`.\n"
)
LENGTH_MSG = (
    "SolveIt: {n} characters of prose since the human's last message, and they did "
    "not ask for depth. Brevity is rule #1 — give the answer plus its proof handle, "
    "and move the audit trail into the artifact you just wrote.\n"
)


REPAIR = (
    "The text you already wrote is on the human's screen and stays there — do not "
    "write it again in other words. Send only the correction: the fixed handle, plus "
    "one sentence if it needs a lead-in.\n"
)


LENGTH_REPAIR = (
    "They have already read it — don't send a shortened rewrite of the same answer. "
    "Say nothing further beyond the handle, and keep the next turn to the answer plus "
    "its proof.\n"
)


def die(msg, repair=REPAIR):
    sys.stderr.write(msg + repair)
    sys.exit(2)


def _final_paragraph(body):
    return body.rsplit("\n\n", 1)[-1].strip()


def _prose(span):
    """The span minus fenced blocks — a draft, diff or script the human asked for
    is payload, not a claim that needs proving."""
    return _FENCE_BLOCK.sub("", span).strip()


def _needs_affordance(body):
    """A turn needs a probe handle when it asserts something the human would have
    to take on trust. Not when it asks them a question, acknowledges an action, or
    carries nothing but the payload they asked for."""
    if not body or body.endswith("?"):
        return False
    if CHECKPOINT.search(body):
        return False
    return not (len(body) < 300 and ACK.search(body) and not CLAIM.search(body))


MULTILINE_MSG = (
    "SolveIt: a runnable command in your response spans multiple lines. The human "
    "copies commands straight out of the chat, and pasting a multi-line command "
    "mangles newlines — every command they run must fit on ONE line. Join steps with "
    "'&&' or ';' onto a single line, or if it genuinely can't be one line, write it as "
    "a task script and hand the human the one-line run command (e.g. "
    "'▶ Verify: python .solve/tasks/<f>/current.py'). No backslash line-continuations, "
    "no multi-line bash/sh/zsh fenced blocks.\n"
)


def _has_multiline_command(text):
    """True if the response contains a command the human would copy that is not
    on a single line: a ▶ affordance line continued with a trailing backslash, or
    a shell-tagged fenced block with more than one command line. A block whose
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


def _only_reading_probes(text):
    """True when every ▶ handle in the turn just opens or searches a file."""
    probes = []
    for line in text.split("\n"):
        if AFFORDANCE not in line:
            continue
        cmd = PROBE_LABEL.sub("", line.split(AFFORDANCE, 1)[1].strip()).lstrip("`")
        if cmd:
            probes.append(cmd)
    return bool(probes) and all(READING_PROBE.match(p) for p in probes)


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
    """(assistant text since the human's last message, that message's text)."""
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
    texts, ran, scripts = [], False, []
    for e in entries[start:]:
        if e.get("type") != "assistant":
            continue
        content = (e.get("message") or {}).get("content")
        if not isinstance(content, list):
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
    span, last_user, ran, scripts = _read_span(path)
    for _ in range(tries):
        if AFFORDANCE in span:
            break
        time.sleep(interval)
        span, last_user, ran, scripts = _read_span(path)
    body = _prose(span)
    for fp in scripts if not ran else []:
        name = os.path.basename(fp)
        if name not in span or not _FENCE_BLOCK.search(span):
            die(SCRIPT_MSG.format(name=name, path=fp))
    if MENU.search(_final_paragraph(body)):
        die(MENU_MSG)
    if PASTE_BACK.search(body):
        die(PASTE_MSG)
    if len(body) > BLOCK_CHARS and not DEPTH.search(last_user):
        die(LENGTH_MSG.format(n=len(body)), LENGTH_REPAIR)
    if AFFORDANCE in span:
        if _has_multiline_command(span):
            die(MULTILINE_MSG)
        if not ran and "▶ Verify" in span:
            die(VERIFY_MSG)
        if not ran and CONFIDENT.search(body) and not HEDGE.search(body):
            die(HEDGE_MSG)
        if CLAIM.search(body) and _only_reading_probes(span):
            die(WEAK_PROBE_MSG)
        return
    if not _needs_affordance(body):
        return
    die(
        "SolveIt: your response since the last user message has no probe/verify "
        "affordance (▶). A claim drawn from reading is a hypothesis, not an answer. "
        "Hand over ONE probe, strongest form first: a `debugger`/`binding.irb` on the "
        "exact line plus the command that hits it and the value to print once stopped; "
        "a console/REPL or task-script probe that prints the real value "
        "('▶ Predict, then run: <cmd>'); '▶ run <test|script>'; and only as a fallback "
        "'▶ nvim +<line> <path>' when the code itself is the answer. Check it "
        "yourself first and say in one line what you saw — the probe is theirs to run "
        "for their own understanding, not a request for a report.\n"
    )


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
