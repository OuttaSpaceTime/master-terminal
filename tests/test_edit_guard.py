import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "home/dot_claude/solveit/hooks/executable_edit-guard.py"


def _load():
    spec = importlib.util.spec_from_file_location("edit_guard", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    r = tmp_path / "repo"
    r.mkdir()
    subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    return r


@pytest.fixture
def run(monkeypatch, capsys):
    def _run(tool, ti, cwd, session="s", transcript=None):
        monkeypatch.delenv("SOLVEIT_OFF", raising=False)
        payload = {"tool_name": tool, "tool_input": ti, "cwd": str(cwd), "session_id": session}
        if transcript is not None:
            path = cwd.parent / "transcript.jsonl"
            path.write_text("".join(json.dumps(e) + "\n" for e in transcript))
            payload["transcript_path"] = str(path)
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        try:
            guard.main()
            return 0, ""
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            return code, capsys.readouterr().err

    return _run


@pytest.fixture
def next_turn(tmp_path):
    def _next(session="s"):
        (tmp_path / "home/.claude/solveit/state" / f"{session}.edits").unlink(missing_ok=True)

    return _next


def test_write_within_cap(repo, run):
    assert run("Write", {"file_path": str(repo / "a.txt"), "content": "x\n" * 20}, repo)[0] == 0


def test_write_over_cap(repo, run):
    code, err = run("Write", {"file_path": str(repo / "a.txt"), "content": "x\n" * 31}, repo)
    assert code == 2 and "ceiling" in err


def test_edit_over_cap(repo, run):
    ti = {"file_path": str(repo / "a.txt"), "old_string": "a\n", "new_string": "y\n" * 35}
    assert run("Edit", ti, repo)[0] == 2


def test_multiedit_sums_added(repo, run):
    ti = {
        "file_path": str(repo / "a.txt"),
        "edits": [{"old_string": "", "new_string": "y\n" * 16}, {"old_string": "", "new_string": "z\n" * 16}],
    }
    assert run("MultiEdit", ti, repo)[0] == 2


def test_write_at_raised_cap(repo, run):
    assert run("Write", {"file_path": str(repo / "a.txt"), "content": "x\n" * 30}, repo)[0] == 0


def test_dirty_within_raised_cap(repo, run):
    (repo / "big.txt").write_text("l\n" * 25)
    assert run("Write", {"file_path": str(repo / "s.txt"), "content": "x\n"}, repo)[0] == 0


def test_total_within_raised_cap(repo, run):
    (repo / "big.txt").write_text("l\n" * 200)
    subprocess.run(["git", "-C", str(repo), "add", "big.txt"], check=True)
    assert run("Write", {"file_path": str(repo / "s.txt"), "content": "x\n"}, repo)[0] == 0


def test_dirty_cap_blocks(repo, run):
    (repo / "big.txt").write_text("l\n" * 35)
    code, err = run("Write", {"file_path": str(repo / "small.txt"), "content": "x\n"}, repo)
    assert code == 2 and "unstaged" in err


def test_total_cap_blocks(repo, run):
    (repo / "big.txt").write_text("l\n" * 305)
    subprocess.run(["git", "-C", str(repo), "add", "big.txt"], check=True)
    code, err = run("Write", {"file_path": str(repo / "small.txt"), "content": "x\n"}, repo)
    assert code == 2 and "total cap" in err


def test_splitting_marker_lifts_the_total_cap(repo, run):
    (repo / "big.txt").write_text("l\n" * 305)
    subprocess.run(["git", "-C", str(repo), "add", "big.txt"], check=True)
    (repo / ".solve").mkdir()
    (repo / ".solve" / "splitting").touch()
    assert run("Write", {"file_path": str(repo / "small.txt"), "content": "x\n"}, repo)[0] == 0


def test_splitting_marker_lifts_the_dirty_cap(repo, run):
    (repo / "big.txt").write_text("l\n" * 35)
    (repo / ".solve").mkdir()
    (repo / ".solve" / "splitting").touch()
    assert run("Write", {"file_path": str(repo / "small.txt"), "content": "x\n"}, repo)[0] == 0


def test_splitting_marker_lifts_the_per_edit_cap(repo, run):
    (repo / ".solve").mkdir()
    (repo / ".solve" / "splitting").touch()
    assert run("Write", {"file_path": str(repo / "a.txt"), "content": "x\n" * 80}, repo)[0] == 0


def test_splitting_marker_keeps_the_turn_edit_cap(repo, run):
    (repo / ".solve").mkdir()
    (repo / ".solve" / "splitting").touch()
    ti = {"file_path": str(repo / "a.txt"), "content": "x\n"}
    for _ in range(guard.EDIT_CAP):
        assert run("Write", ti, repo, session="turn")[0] == 0
    code, err = run("Write", ti, repo, session="turn")
    assert code == 2 and "hand back" in err


def test_splitting_marker_dies_with_the_session(repo, run, next_turn):
    (repo / "big.txt").write_text("l\n" * 305)
    subprocess.run(["git", "-C", str(repo), "add", "big.txt"], check=True)
    (repo / ".solve").mkdir()
    marker = repo / ".solve" / "splitting"
    marker.touch()
    ti = {"file_path": str(repo / "small.txt"), "content": "x\n"}
    assert run("Write", ti, repo, session="chat1")[0] == 0
    assert marker.read_text().strip() == "chat1"
    next_turn("chat1")
    assert run("Write", ti, repo, session="chat1")[0] == 0
    code, err = run("Write", ti, repo, session="chat2")
    assert code == 2 and "total cap" in err
    assert not marker.exists()


def test_agent_cannot_drop_the_marker_itself(repo, run):
    ti = {"file_path": str(repo / ".solve" / "splitting"), "content": ""}
    code, err = run("Write", ti, repo)
    assert code == 2 and "human" in err


def test_splitting_marker_never_lifts_the_task_folder_edit_ceiling(repo, run):
    a = repo / ".solve" / "tasks" / "probe"
    a.mkdir(parents=True)
    (a / "t.md").write_text("# probe\n")
    (repo / ".solve" / "splitting").touch()
    code, err = run("Write", {"file_path": str(a / "01.py"), "content": "x\n" * 80}, repo)
    assert code == 2 and "ceiling" in err


def test_archived_task_scripts_never_block_the_next_current(repo, run):
    a = repo / ".solve" / "tasks" / "probe"
    a.mkdir(parents=True)
    subprocess.run(["git", "-C", str(a), "init", "-q"], check=True)
    for n in range(1, 6):
        (a / f"0{n}-step.rb").write_text("l\n" * 8)
    assert run("Write", {"file_path": str(a / "current.rb"), "content": "x\n" * 8}, repo)[0] == 0


def test_warn_between_150_and_300(repo, run, capsys):
    (repo / "big.txt").write_text("l\n" * 200)
    subprocess.run(["git", "-C", str(repo), "add", "big.txt"], check=True)
    code = run("Write", {"file_path": str(repo / "s.txt"), "content": "x\n"}, repo)[0]
    out = capsys.readouterr().out
    assert code == 0 and "150" in out


def test_second_task_folder_blocked(repo, run):
    a = repo / ".solve" / "tasks" / "a"
    a.mkdir(parents=True)
    (a / "t.md").write_text("# a\n")
    assert run("Write", {"file_path": str(a / "01.py"), "content": "print(1)\n"}, repo, session="s1")[0] == 0
    b = repo / ".solve" / "tasks" / "b"
    b.mkdir(parents=True)
    code, err = run("Write", {"file_path": str(b / "01.py"), "content": "print(2)\n"}, repo, session="s1")
    assert code == 2 and "task folder" in err


def test_project_edits_past_the_turn_cap_are_denied(repo, run):
    ti = {"file_path": str(repo / "a.txt"), "content": "x\n"}
    for _ in range(guard.EDIT_CAP):
        assert run("Write", ti, repo, session="turn")[0] == 0
    code, err = run("Write", ti, repo, session="turn")
    assert code == 2 and "hand back" in err


def test_task_script_writes_do_not_count_toward_the_turn(repo, run):
    a = repo / ".solve" / "tasks" / "probe"
    a.mkdir(parents=True)
    for i in range(4):
        ti = {"file_path": str(a / f"0{i}.py"), "content": "x\n"}
        assert run("Write", ti, repo, session="scratch")[0] == 0


def test_same_task_folder_ok(repo, run):
    a = repo / ".solve" / "tasks" / "a"
    a.mkdir(parents=True)
    (a / "t.md").write_text("# a\n")
    assert run("Write", {"file_path": str(a / "01.py"), "content": "x\n"}, repo, session="s2")[0] == 0
    assert run("Write", {"file_path": str(a / "02.py"), "content": "x\n"}, repo, session="s2")[0] == 0


def test_write_lands_without_a_go_from_the_human(repo, run):
    assert run("Write", {"file_path": str(repo / "a.txt"), "content": "x\n"}, repo)[0] == 0


def test_only_one_project_edit_lands_per_turn(repo, run):
    ti = {"file_path": str(repo / "a.txt"), "content": "x\n"}
    assert run("Write", ti, repo, session="one")[0] == 0
    code, err = run("Write", ti, repo, session="one")
    assert code == 2 and "hand back" in err


def _prompt(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def _write_current(tid="c1"):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": tid, "name": "Write",
         "input": {"file_path": "/repo/.solve/tasks/t/current.rb"}}]}}


def _result(tid="c1", is_error=False):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": "ok", "is_error": is_error}]}}


def _human(cmd, out=""):
    return [_prompt(f"<bash-input>{cmd}</bash-input>"),
            _prompt(f"<bash-stdout>{out}</bash-stdout><bash-stderr></bash-stderr>")]


APP = "app.rb"


CURRENT = ".solve/tasks/t/current.rb"


def test_project_write_lands_while_current_is_unrun(repo, run):
    t = [_prompt("go"), _write_current(), _result(), _prompt("next")]
    assert run("Write", {"file_path": str(repo / APP), "content": "x\n"}, repo, transcript=t)[0] == 0


def test_next_current_waits_for_the_human_to_run_current(repo, run):
    t = [_prompt("go"), _write_current(), _result(), _prompt("next")]
    code, err = run("Write", {"file_path": str(repo / CURRENT), "content": "x\n"}, repo, transcript=t)
    assert code == 2 and "current.rb" in err and "`! " in err


def test_next_current_in_another_language_waits_too(repo, run):
    (repo / CURRENT).parent.mkdir(parents=True)
    (repo / CURRENT).write_text("p 1\n")
    t = [_prompt("go"), _write_current(), _result(), _prompt("next")]
    current_py = repo / ".solve/tasks/t/current.py"
    assert run("Write", {"file_path": str(current_py), "content": "x\n"}, repo, transcript=t)[0] == 2


def test_next_current_lands_once_the_human_ran_current(repo, run):
    t = [_prompt("go"), _write_current(), _result(),
         *_human("ruby .solve/tasks/t/current.rb", "total: 2"), _prompt("next")]
    assert run("Write", {"file_path": str(repo / CURRENT), "content": "x\n"}, repo, transcript=t)[0] == 0


def test_another_human_command_is_not_a_run_of_current(repo, run):
    t = [_prompt("go"), _write_current(), _result(), *_human("git status"), _prompt("next")]
    assert run("Write", {"file_path": str(repo / CURRENT), "content": "x\n"}, repo, transcript=t)[0] == 2


def test_a_human_run_clears_a_current_written_after_the_last_prompt(repo, run):
    t = [_prompt("go"), _write_current(), _result(), _prompt("next"),
         _write_current("c2"), _result("c2"), *_human("ruby .solve/tasks/t/current.rb"), _prompt("go on")]
    assert run("Write", {"file_path": str(repo / CURRENT), "content": "x\n"}, repo, transcript=t)[0] == 0


def test_the_turn_a_human_run_starts_only_reads(repo, run):
    t = [_prompt("go"), _write_current(), _result(), *_human("ruby .solve/tasks/t/current.rb")]
    code, err = run("Write", {"file_path": str(repo / APP), "content": "x\n"}, repo, transcript=t)
    assert code == 2 and "next message" in err


def test_the_turn_a_human_run_starts_does_not_write_the_next_current(repo, run):
    t = [_prompt("go"), _write_current(), _result(), *_human("ruby .solve/tasks/t/current.rb")]
    current = repo / ".solve/tasks/t/current.rb"
    code, err = run("Write", {"file_path": str(current), "content": "x\n"}, repo, transcript=t)
    assert code == 2 and "next message" in err


def test_current_written_this_turn_does_not_hold_the_turn(repo, run):
    t = [_prompt("go"), _write_current(), _result()]
    assert run("Write", {"file_path": str(repo / CURRENT), "content": "x\n"}, repo, transcript=t)[0] == 0


def test_denied_current_write_holds_nothing(repo, run):
    t = [_prompt("go"), _write_current(), _result(is_error=True), _prompt("next")]
    assert run("Write", {"file_path": str(repo / CURRENT), "content": "x\n"}, repo, transcript=t)[0] == 0


def test_fixing_the_unrun_current_in_place_is_allowed(repo, run):
    (repo / CURRENT).parent.mkdir(parents=True)
    (repo / CURRENT).write_text("p 1\n")
    t = [_prompt("go"), _write_current(), _result(), _prompt("check X instead")]
    assert run("Write", {"file_path": str(repo / CURRENT), "content": "x\n"}, repo, transcript=t)[0] == 0
