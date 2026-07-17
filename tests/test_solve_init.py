import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "home/dot_claude/solveit/hooks/executable_solve-init.py"


def _load():
    spec = importlib.util.spec_from_file_location("solve_init", HOOK)
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
    def _run(cwd, session="s", off=False):
        if off:
            monkeypatch.setenv("SOLVEIT_OFF", "1")
        else:
            monkeypatch.delenv("SOLVEIT_OFF", raising=False)
        payload = {"session_id": session, "cwd": str(cwd)}
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        guard.main()
        return capsys.readouterr().out

    return _run


def exclude_text(repo):
    p = repo / ".git" / "info" / "exclude"
    return p.read_text() if p.exists() else ""


def test_first_prompt_adds_exclude_and_context(repo, run):
    out = run(repo, session="s1")
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "SolveIt is on" in ctx
    assert ".solve/" in exclude_text(repo)


def test_second_prompt_is_noop(repo, run):
    run(repo, session="s2")
    assert run(repo, session="s2") == ""


def test_allowlist_injected(repo, run):
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(npm test:*)"]}})
    )
    ctx = json.loads(run(repo, session="s3"))["hookSpecificOutput"]["additionalContext"]
    assert "ALLOWLISTED" in ctx and "`npm test:*`" in ctx


def test_solveit_off_noop(repo, run):
    assert run(repo, session="s4", off=True) == ""
