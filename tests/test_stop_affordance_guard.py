import importlib.util, io, json, sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "home/dot_claude/solveit/hooks/executable_stop-affordance-guard.py"


def _load():
    spec = importlib.util.spec_from_file_location("stop_affordance_guard", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load()


def _user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def _tool_result(tid="t1"):
    return {"type": "user", "message": {"role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tid, "content": "ok"}]}}


def _assistant(*blocks):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def _text(t):
    return {"type": "text", "text": t}


def _thinking(t):
    return {"type": "thinking", "thinking": t}


@pytest.fixture
def run(tmp_path, monkeypatch, capsys):
    def _run(entries, stop_hook_active=False):
        monkeypatch.delenv("SOLVEIT_OFF", raising=False)
        monkeypatch.setenv("STOP_GUARD_POLL", "0")
        p = tmp_path / "transcript.jsonl"
        p.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
        payload = {"transcript_path": str(p), "stop_hook_active": stop_hook_active}
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        try:
            guard.main()
            return 0, capsys.readouterr().err
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            return code, capsys.readouterr().err

    return _run


def test_blocks_without_affordance(run):
    code, err = run([_user("trace this"), _assistant(_text("Confident synthesis. No probe."))])
    assert code == 2
    assert "▶" in err


def test_passes_with_affordance(run):
    code, _ = run([_user("trace this"), _assistant(_text("Look here.\n▶ Predict, then run: foo.rb"))])
    assert code == 0


def test_only_checks_since_last_user_message(run):
    code, _ = run([
        _user("first"), _assistant(_text("earlier ▶ Verify: x")),
        _user("second"), _assistant(_text("plain claim, nothing to run")),
    ])
    assert code == 2


def test_tool_result_is_not_the_anchor(run):
    code, _ = run([
        _user("do it"),
        _assistant(_text("running a probe ▶ Predict, then run: foo")),
        _tool_result(),
        _assistant(_text("here is the result, plainly stated")),
    ])
    assert code == 0


def test_thinking_block_does_not_count(run):
    code, _ = run([_user("q"), _assistant(_thinking("▶ Predict: internal"), _text("shown answer, no probe"))])
    assert code == 2


def test_blocks_multiline_bash_fence(run):
    text = "Run it:\n▶ Verify:\n```bash\ncd repo\nmake test\n```"
    code, err = run([_user("q"), _assistant(_text(text))])
    assert code == 2
    assert "one line" in err.lower()


def test_passes_single_line_bash_fence(run):
    text = "Run it:\n▶ Verify:\n```bash\ncd repo && make test\n```"
    code, _ = run([_user("q"), _assistant(_text(text))])
    assert code == 0


def test_blocks_backslash_continuation_on_affordance(run):
    text = "▶ Predict, then run: grep foo \\\n  bar baz"
    code, err = run([_user("q"), _assistant(_text(text))])
    assert code == 2
    assert "one line" in err.lower()


def test_multiline_code_sketch_is_not_a_command(run):
    text = "Read this:\n▶ nvim +10 foo.py\n```python\ndef f():\n    return 1\n```"
    code, _ = run([_user("q"), _assistant(_text(text))])
    assert code == 0


def test_stop_hook_active_short_circuits(run):
    code, _ = run([_user("q"), _assistant(_text("no probe here"))], stop_hook_active=True)
    assert code == 0


def test_solveit_off_short_circuits(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SOLVEIT_OFF", "1")
    p = tmp_path / "t.jsonl"
    p.write_text(json.dumps(_assistant(_text("no probe here"))) + "\n")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"transcript_path": str(p)})))
    code = 0
    try:
        guard.main()
    except SystemExit as e:
        code = e.code
    assert code == 0


def test_polls_until_affordance_flushes(tmp_path, monkeypatch):
    """Regression: the turn's final assistant text is flushed to the transcript
    AFTER the Stop hook fires (Claude Code write race, issue #21751). The hook
    must poll and pass once the ▶ appears, not false-block on the stale read."""
    monkeypatch.delenv("SOLVEIT_OFF", raising=False)
    monkeypatch.setenv("STOP_GUARD_POLL", "5")
    monkeypatch.setenv("STOP_GUARD_POLL_INTERVAL", "0")
    p = tmp_path / "transcript.jsonl"
    p.write_text(json.dumps(_user("trace this")) + "\n")

    calls = {"n": 0}

    def fake_sleep(_):
        calls["n"] += 1
        if calls["n"] == 2:
            with open(p, "a") as f:
                f.write(json.dumps(_assistant(_text("answer\n▶ Verify: echo hi"))) + "\n")

    monkeypatch.setattr(guard.time, "sleep", fake_sleep)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"transcript_path": str(p)})))
    code = 0
    try:
        guard.main()
    except SystemExit as e:
        code = e.code
    assert code == 0
    assert calls["n"] >= 2
