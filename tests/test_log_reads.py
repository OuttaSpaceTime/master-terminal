import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "home/dot_claude/solveit/hooks/executable_log-reads.py"


def _load():
    spec = importlib.util.spec_from_file_location("log_reads", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    return r


@pytest.fixture
def run(monkeypatch):
    def _run(tool, ti, cwd, off=False):
        if off:
            monkeypatch.setenv("SOLVEIT_OFF", "1")
        else:
            monkeypatch.delenv("SOLVEIT_OFF", raising=False)
        payload = {"tool_name": tool, "tool_input": ti, "cwd": str(cwd)}
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        guard.main()

    return _run


def log_lines(repo):
    p = repo / ".solve" / "reads.log"
    return p.read_text().splitlines() if p.exists() else []


def test_read_logged(repo, run):
    run("Read", {"file_path": "foo.py"}, repo)
    assert log_lines(repo)[-1].endswith("\tRead\tfoo.py")


def test_grep_format_includes_path_and_glob(repo, run):
    run("Grep", {"pattern": "x", "path": "src", "glob": "*.py"}, repo)
    assert log_lines(repo)[-1].endswith("\tGrep\tx  (src, glob=*.py)")


def test_glob_format_includes_path(repo, run):
    run("Glob", {"pattern": "**/*.py", "path": "lib"}, repo)
    assert log_lines(repo)[-1].endswith("\tGlob\t**/*.py  (in lib)")


def test_other_tool_not_logged(repo, run):
    run("Bash", {"command": "ls"}, repo)
    assert log_lines(repo) == []


def test_solveit_off_skips(repo, run):
    run("Read", {"file_path": "foo.py"}, repo, off=True)
    assert log_lines(repo) == []


def test_target_for_grep_bare():
    assert guard.target_for("Grep", {"pattern": "x"}) == "x"
