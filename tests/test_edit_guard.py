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
    def _run(tool, ti, cwd, session="s"):
        monkeypatch.delenv("SOLVEIT_OFF", raising=False)
        payload = {"tool_name": tool, "tool_input": ti, "cwd": str(cwd), "session_id": session}
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        try:
            guard.main()
            return 0, ""
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            return code, capsys.readouterr().err

    return _run


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


def test_splitting_marker_dies_with_the_session(repo, run):
    (repo / "big.txt").write_text("l\n" * 305)
    subprocess.run(["git", "-C", str(repo), "add", "big.txt"], check=True)
    (repo / ".solve").mkdir()
    marker = repo / ".solve" / "splitting"
    marker.touch()
    ti = {"file_path": str(repo / "small.txt"), "content": "x\n"}
    assert run("Write", ti, repo, session="chat1")[0] == 0
    assert marker.read_text().strip() == "chat1"
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


def test_splitting_marker_never_lifts_the_task_repo_dirty_cap(repo, run):
    a = repo / ".solve" / "tasks" / "probe"
    a.mkdir(parents=True)
    (a / "t.md").write_text("# probe\n")
    subprocess.run(["git", "-C", str(a), "init", "-q"], check=True)
    (a / "big.py").write_text("l\n" * 35)
    (repo / ".solve" / "splitting").touch()
    code, err = run("Write", {"file_path": str(a / "02.py"), "content": "x\n"}, repo)
    assert code == 2 and "unstaged" in err


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
