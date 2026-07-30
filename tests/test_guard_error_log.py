"""Every SolveIt hook fails open. It must still leave a trace, or a parser crash
silently unlocks the jail (bash-guard) or the caps (edit-guard)."""
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "home/dot_claude/solveit/hooks"
CASES = [
    ("bash-guard", "executable_bash-guard.py"),
    ("edit-guard", "executable_edit-guard.py"),
    ("stop-affordance-guard", "executable_stop-affordance-guard.py"),
]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HOOKS / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("name,filename", CASES)
def test_exception_is_logged_and_fails_open(name, filename, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SOLVEIT_OFF", raising=False)
    mod = _load(name, filename)
    monkeypatch.setattr(sys, "stdin", io.StringIO("{ this is not json"))
    with pytest.raises(SystemExit) as e:
        mod.run_guarded()
    assert e.value.code == 0
    log = tmp_path / ".claude/solveit/guard-errors.log"
    assert log.exists()
    assert name in log.read_text()


@pytest.mark.parametrize("name,filename", CASES)
def test_clean_run_logs_nothing(name, filename, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SOLVEIT_OFF", "1")
    mod = _load(name, filename)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({})))
    try:
        mod.run_guarded()  # bash/edit-guard return; the stop hook always exits 0
    except SystemExit as e:
        assert e.code == 0
    assert not (tmp_path / ".claude/solveit/guard-errors.log").exists()
