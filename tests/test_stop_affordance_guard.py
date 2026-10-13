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


def _tool_result(tid="t1", is_error=False):
    return {"type": "user", "message": {"role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tid, "content": "ok", "is_error": is_error}]}}


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


def test_claim_without_a_handle_passes(run):
    text = "Looks like the callback leaves searchable_text empty because id is nil on create."
    code, _ = run([_user("why?"), _assistant(_text(text))])
    assert code == 0


def test_only_checks_since_last_user_message(run):
    code, _ = run([
        _user("first"), _assistant(_text("Did it.\n\nWant me to rename it too?")),
        _user("second"), _assistant(_text("Renamed.")),
    ])
    assert code == 0


def test_tool_result_is_not_the_anchor(run):
    code, err = run([
        _user("do it"),
        _assistant(_text("Run it and paste the tail.")),
        _tool_result(),
        _assistant(_text("Done.")),
    ])
    assert code == 2
    assert "paste" in err.lower()


def test_thinking_block_does_not_count(run):
    code, _ = run([_user("q"), _assistant(_thinking("then paste the output here"), _text("Done."))])
    assert code == 0


def test_blocks_multiline_bash_fence(run):
    text = "Run it:\n▶ Verify:\n```bash\ncd repo\nmake test\n```"
    code, err = run([_user("q"), _assistant(_text(text))])
    assert code == 2
    assert "one line" in err.lower()


def test_blocks_multiline_bash_fence_without_a_handle(run):
    text = "Run it:\n```bash\ncd repo\nmake test\n```"
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
    code, _ = run([_user("q"), _assistant(_text("Want me to do it?"))], stop_hook_active=True)
    assert code == 0


def test_solveit_off_short_circuits(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SOLVEIT_OFF", "1")
    p = tmp_path / "t.jsonl"
    p.write_text(json.dumps(_assistant(_text("Want me to do it?"))) + "\n")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"transcript_path": str(p)})))
    code = 0
    try:
        guard.main()
    except SystemExit as e:
        code = e.code
    assert code == 0


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


def _tool_use(name="Bash"):
    return {"type": "tool_use", "id": "t1", "name": name, "input": {}}


def test_blocks_unhedged_claim_on_read_only_turn(run):
    text = "Confirmed: the callback proves searchable_text stays empty.\n▶ nvim +239 component.rb"
    code, err = run([_user("trace it"), _assistant(_text(text))])
    assert code == 2
    assert "only read" in err.lower()


def test_blocks_unhedged_claim_without_a_handle(run):
    text = "Confirmed: the callback proves searchable_text stays empty."
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


def _run_polling(tmp_path, monkeypatch, entries, late_entry):
    """Run the hook with polling on; `late_entry` lands in the transcript on the
    second sleep. Returns (exit code, number of sleeps)."""
    monkeypatch.delenv("SOLVEIT_OFF", raising=False)
    monkeypatch.setenv("STOP_GUARD_POLL", "5")
    monkeypatch.setenv("STOP_GUARD_POLL_INTERVAL", "0")
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    sleeps = {"n": 0}

    def fake_sleep(_):
        sleeps["n"] += 1
        if sleeps["n"] == 2 and late_entry:
            with open(p, "a") as f:
                f.write(json.dumps(late_entry) + "\n")

    monkeypatch.setattr(guard.time, "sleep", fake_sleep)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"transcript_path": str(p)})))
    try:
        guard.main()
        return 0, sleeps["n"]
    except SystemExit as e:
        return e.code, sleeps["n"]


def test_waits_for_the_final_message_then_stops_waiting(tmp_path, monkeypatch):
    """Regression: the turn's final assistant text is flushed to the transcript
    AFTER the Stop hook fires (Claude Code write race, issue #21751). The hook
    waits until that text lands, then checks it without waiting further."""
    code, sleeps = _run_polling(
        tmp_path, monkeypatch,
        [_user("next"), _assistant(_bash()), _tool_result("b1")],
        _assistant(_text("Did it.\n\nWant me to rename it too?")),
    )
    assert (code, sleeps) == (2, 2)


def test_no_wait_when_the_final_message_is_already_there(tmp_path, monkeypatch):
    code, sleeps = _run_polling(
        tmp_path, monkeypatch,
        [_user("q"), _assistant(_text("Looks like it is fine."))],
        None,
    )
    assert (code, sleeps) == (0, 0)


def _write(path, tid="w1"):
    return {"type": "tool_use", "id": tid, "name": "Write", "input": {"file_path": path}}


def _bash(cmd="ruby x", tid="b1"):
    return {"type": "tool_use", "id": tid, "name": "Bash", "input": {"command": cmd}}


RUN_CURRENT = "ruby .solve/tasks/t/current.rb"


def test_blocks_task_script_written_but_not_shown(run):
    code, err = run([
        _user("probe it"),
        _assistant(_write("/repo/.solve/tasks/t/01-probe-token-expiry.py"),
                   _text("Written.\n▶ Try: python .solve/tasks/t/01-probe-token-expiry.py")),
    ])
    assert code == 2
    assert "01-probe-token-expiry.py" in err


def test_task_script_shown_passes(run):
    text = (
        "Prints the token expiry for the fixture user.\n"
        "```python\n# python .solve/tasks/t/01-probe-token-expiry.py\nprint(user.token)\n```\n"
        "▶ nvim .solve/tasks/t/01-probe-token-expiry.py"
    )
    code, _ = run([
        _user("probe it"),
        _assistant(_write("/repo/.solve/tasks/t/01-probe-token-expiry.py"), _text(text)),
    ])
    assert code == 0


def test_task_script_written_and_run_in_one_turn_needs_no_listing(run):
    code, _ = run([
        _user("probe it"),
        _assistant(_write("/repo/.solve/tasks/t/current.rb"),
                   _bash(RUN_CURRENT),
                   _text("Expiry is 3600.")),
    ])
    assert code == 0


def test_bash_task_script_listing_is_not_a_multiline_command(run):
    text = (
        "Runs the auth specs.\n"
        "```bash\n# bash .solve/tasks/t/01-run-auth-specs.sh\ncd repo\nbundle exec rspec spec/auth\n```\n"
        "▶ nvim .solve/tasks/t/01-run-auth-specs.sh"
    )
    code, _ = run([
        _user("run the auth specs"),
        _assistant(_write("/repo/.solve/tasks/t/01-run-auth-specs.sh"), _text(text)),
    ])
    assert code == 0


def test_blocks_project_change_without_running_current(run):
    code, err = run([_user("next"), _assistant(_write("/repo/app/models/user.rb"), _text("Changed the scope."))])
    assert code == 2
    assert "current.<ext>" in err


def test_project_change_verified_by_current_passes(run):
    code, _ = run([_user("next"), _assistant(
        _write("/repo/app/models/user.rb"),
        _write("/repo/.solve/tasks/t/current.rb", "w2"),
        _bash(RUN_CURRENT),
        _text("total is 2; the SQL filters archived rows."),
    )])
    assert code == 0


def test_run_before_the_last_change_does_not_count(run):
    code, err = run([_user("next"), _assistant(
        _write("/repo/.solve/tasks/t/current.rb"),
        _bash(RUN_CURRENT),
        _write("/repo/app/models/user.rb", "w2"),
        _text("total is 2."),
    )])
    assert code == 2
    assert "user.rb" in err


def test_running_an_archived_script_does_not_verify(run):
    code, err = run([_user("next"), _assistant(
        _write("/repo/app/models/user.rb"),
        _bash("ruby .solve/tasks/t/02-probe-scope.rb"),
        _text("total is 2."),
    )])
    assert code == 2
    assert "current.<ext>" in err


def test_archiving_current_is_not_a_run(run):
    code, err = run([_user("next"), _assistant(
        _write("/repo/app/models/user.rb"),
        _bash("mv .solve/tasks/t/current.rb .solve/tasks/t/03-total.rb"),
        _text("Archived the old check."),
    )])
    assert code == 2
    assert "current.<ext>" in err


def test_reading_current_is_not_a_run(run):
    code, err = run([_user("next"), _assistant(
        _write("/repo/app/models/user.rb"),
        _bash("cat .solve/tasks/t/current.rb"),
        _text("total is 2."),
    )])
    assert code == 2
    assert "current.<ext>" in err


def test_runner_or_piped_run_of_current_counts(run):
    for cmd in ("bin/rails runner .solve/tasks/t/current.rb", "ruby .solve/tasks/t/current.rb | tail -3"):
        code, _ = run([_user("next"), _assistant(
            _write("/repo/app/models/user.rb"), _bash(cmd), _text("total is 2."),
        )])
        assert code == 0, cmd


def test_rewritten_current_must_run(run):
    code, err = run([_user("next"), _assistant(_write("/repo/.solve/tasks/t/current.rb"), _text("Wrote the check."))])
    assert code == 2
    assert "current.<ext>" in err


def test_failing_run_of_current_still_counts(run):
    code, _ = run([
        _user("next"),
        _assistant(_write("/repo/app/models/user.rb"), _bash(RUN_CURRENT)),
        _tool_result("b1", is_error=True),
        _assistant(_text("Red as expected: total is 3, archived row still counted.")),
    ])
    assert code == 0


def test_denied_write_does_not_need_a_run(run):
    code, _ = run([
        _user("next"),
        _assistant(_write("/repo/app/a.rb"), _bash(RUN_CURRENT)),
        _assistant(_write("/repo/app/b.rb", "w2")),
        _tool_result("w2", is_error=True),
        _assistant(_text("a.rb landed; b.rb waits for the next step.")),
    ])
    assert code == 0


def test_block_message_says_not_to_resend_the_answer(run):
    text = "Confirmed: the cause is the second callback."
    code, err = run([_user("trace it"), _assistant(_text(text))])
    assert code == 2
    assert "on the human's screen" in err
    assert "Send only the correction" in err


def test_repair_note_is_on_every_block_path(run):
    paths = [
        [_user("trace this"), _assistant(_text("Confirmed: the callback proves it."))],
        [_user("go"), _assistant(_text("Did the thing. Want me to also rename it?"))],
        [_user("go"), _assistant(_text("It is done.\nPaste the output here."))],
        [_user("next"), _assistant(_write("/repo/app/a.rb"), _text("Changed it."))],
    ]
    for entries in paths:
        code, err = run(entries)
        assert code == 2, entries
        assert "Send only the correction" in err, entries


def test_length_block_asks_for_no_rewrite_at_all(run):
    text = "x " * 1200 + "\n▶ Verify: echo hi"
    code, err = run([_user("shorten it"), _assistant(_text(text))])
    assert code == 2
    assert "shortened rewrite" in err
    assert "Send only the correction" not in err


def test_bare_why_question_does_not_lift_the_length_cap(run):
    text = "x " * 1200 + "\n▶ Try: echo hi"
    code, err = run([_user("hold on why did we remove the before parameter?"),
                     _assistant(_text(text))])
    assert code == 2
    assert "brevity" in err.lower()
