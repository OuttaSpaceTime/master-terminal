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
    text = "Run it:\n▶ Try:\n```bash\ncd repo && make test\n```"
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


def test_question_to_human_needs_no_affordance(run):
    code, _ = run([_user("which key?"), _assistant(_text("Two `g` groups exist. Which one do you mean?"))])
    assert code == 0


def test_short_ack_needs_no_affordance(run):
    code, _ = run([_user("apply it"), _assistant(_text("Applied cleanly. Restart nvim and press `<leader>fy`."))])
    assert code == 0


def test_payload_only_turn_needs_no_affordance(run):
    text = "```markdown\nI think this does not fix the underlying issue.\n\nThe loop came from buildParams().\n```"
    code, _ = run([_user("draft the comment"), _assistant(_text(text))])
    assert code == 0


def test_claim_still_needs_affordance(run):
    text = "It is the callback: because id is nil on create, searchable_text stores empty."
    code, err = run([_user("why?"), _assistant(_text(text))])
    assert code == 2
    assert "▶" in err


def test_blocks_trailing_menu(run):
    text = "Reverted it.\n\nWant me to apply option A in the job instead?"
    code, err = run([_user("fix it"), _assistant(_text(text))])
    assert code == 2
    assert "menu" in err.lower()


def test_mid_turn_should_i_is_not_a_menu(run):
    text = "I wondered whether I should inline it; the answer is no.\n▶ Try: bin/rails test"
    code, _ = run([_user("q"), _assistant(_text(text))])
    assert code == 0


def test_blocks_asking_the_human_to_paste_output(run):
    text = "Run it and paste the tail; then I'll write the harness.\n▶ Verify: bash setup.sh"
    code, err = run([_user("go"), _assistant(_text(text))])
    assert code == 2
    assert "paste" in err.lower()


def test_blocks_wall_of_text_when_no_depth_asked(run):
    text = "x " * 1200 + "\n▶ Verify: echo hi"
    code, err = run([_user("shorten it"), _assistant(_text(text))])
    assert code == 2
    assert "brevity" in err.lower()


def test_long_answer_allowed_when_depth_asked(run):
    text = "x " * 1200 + "\n▶ Try: echo hi"
    code, _ = run([_user("explain why in detail"), _assistant(_text(text))])
    assert code == 0


def test_payload_fence_does_not_count_toward_length(run):
    text = "Drafted:\n```md\n" + "y " * 1500 + "\n```\n▶ nvim +1 draft.md"
    code, _ = run([_user("draft it"), _assistant(_text(text))])
    assert code == 0


def test_checkpoint_report_needs_no_affordance(run):
    text = "31 unstaged lines in the repo — stage what you accept, or commit before I write more."
    code, _ = run([_user("go on"), _assistant(_text(text))])
    assert code == 0


def _tool_use(name="Bash"):
    return {"type": "tool_use", "id": "t1", "name": name, "input": {}}


def test_verify_marker_requires_having_run_something(run):
    text = "Looks like the guard is fine.\n▶ Verify: bin/rails test"
    code, err = run([_user("check it"), _assistant(_text(text))])
    assert code == 2
    assert "▶ Try" in err


def test_try_marker_is_fine_without_running(run):
    text = "Looks like the guard is fine.\n▶ Try: bin/rails test"
    code, _ = run([_user("check it"), _assistant(_text(text))])
    assert code == 0


def test_verify_marker_is_fine_when_something_ran(run):
    text = "Green, 17 runs 0 failures.\n▶ Verify: bin/rails test"
    code, _ = run([_user("run it"), _assistant(_tool_use(), _text(text))])
    assert code == 0


def test_blocks_unhedged_claim_on_read_only_turn(run):
    text = "Confirmed: the callback proves searchable_text stays empty.\n▶ nvim +239 component.rb"
    code, err = run([_user("trace it"), _assistant(_text(text))])
    assert code == 2
    assert "only read" in err.lower()


def test_hedged_claim_on_read_only_turn_passes(run):
    text = "Looks like the callback leaves searchable_text empty.\n▶ nvim +239 component.rb"
    code, _ = run([_user("trace it"), _assistant(_text(text))])
    assert code == 0


def test_confident_claim_passes_when_the_turn_ran_something(run):
    text = "Confirmed: 17 runs, 0 failures.\n▶ Verify: bin/rails test"
    code, _ = run([_user("run it"), _assistant(_tool_use(), _text(text))])
    assert code == 0


def test_blocks_claim_whose_only_probe_is_a_reading_assignment(run):
    text = "Looks like searchable_text stays empty because id is nil on create.\n▶ nvim +239 component.rb"
    code, err = run([_user("trace it"), _assistant(_text(text))])
    assert code == 2
    assert "reading assignment" in err.lower()


def test_blocks_claim_whose_only_probe_is_a_grep(run):
    text = "Looks like the cause is the second callback.\n▶ Try: rg searchable_text app/models"
    code, err = run([_user("trace it"), _assistant(_text(text))])
    assert code == 2
    assert "reading assignment" in err.lower()


def test_breakpoint_probe_satisfies_a_claim(run):
    text = ("Looks like id is nil there because the callback runs before insert.\n"
            "▶ Try: add `debugger` at component.rb:239, run bin/rails test test/component_test.rb, print self.id")
    code, _ = run([_user("trace it"), _assistant(_text(text))])
    assert code == 0


def test_console_probe_satisfies_a_claim(run):
    text = "Looks like the ORDER BY is reversed, which is why page 2 repeats.\n▶ Try: bin/rails runner .solve/tasks/2026-08-06-order/01-print-sql.rb"
    code, _ = run([_user("trace it"), _assistant(_text(text))])
    assert code == 0


def test_reading_probe_is_fine_next_to_an_execution_probe(run):
    text = ("Looks like the callback is the reason.\n"
            "▶ nvim +239 component.rb\n▶ Try: bin/rails test test/component_test.rb")
    code, _ = run([_user("trace it"), _assistant(_text(text))])
    assert code == 0


def test_reading_probe_is_fine_without_a_claim(run):
    text = "Two callbacks touch that column.\n▶ nvim +239 component.rb"
    code, _ = run([_user("where is it set?"), _assistant(_text(text))])
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
                f.write(json.dumps(_assistant(_text("answer\n▶ Try: echo hi"))) + "\n")

    monkeypatch.setattr(guard.time, "sleep", fake_sleep)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"transcript_path": str(p)})))
    code = 0
    try:
        guard.main()
    except SystemExit as e:
        code = e.code
    assert code == 0
    assert calls["n"] >= 2
