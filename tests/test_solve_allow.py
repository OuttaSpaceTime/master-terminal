import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "home/dot_claude/solveit/hooks/solve_allow.py"


def _load():
    spec = importlib.util.spec_from_file_location("solve_allow", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sa = _load()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    r = tmp_path / "repo"
    r.mkdir()
    subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    return r


def test_allow_patterns_extracts_only_bash(repo):
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(npm test:*)", "Read(//foo/**)", "Bash(ls*)"]}})
    )
    assert sa.allow_patterns(repo) == ["npm test:*", "ls*"]


def test_allow_patterns_merges_local_after_project(repo):
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(a:*)"]}})
    )
    (repo / ".claude" / "settings.local.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(b:*)"]}})
    )
    assert sa.allow_patterns(repo) == ["a:*", "b:*"]


def test_add_pattern_new_then_dedup(tmp_path):
    fp = str(tmp_path / "settings.json")
    assert sa.add_pattern(fp, "npm run x:*") is True
    assert sa.add_pattern(fp, "npm run x:*") is False
    data = json.load(open(fp))
    assert data["permissions"]["allow"] == ["Bash(npm run x:*)"]


def test_remove_pattern(tmp_path):
    fp = str(tmp_path / "settings.json")
    sa.add_pattern(fp, "foo:*")
    assert sa.remove_pattern(fp, "foo:*") is True
    assert sa.remove_pattern(fp, "foo:*") is False
    assert json.load(open(fp))["permissions"]["allow"] == []
