import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "home/dot_claude/solveit/hooks/executable_bash-guard.py"


def _load():
    spec = importlib.util.spec_from_file_location("bash_guard", HOOK)
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
def run(monkeypatch, capsys, tmp_path):
    def _run(cmd, cwd, go=True):
        monkeypatch.delenv("SOLVEIT_OFF", raising=False)
        flag = tmp_path / "home/.claude/solveit/state/s.go"
        flag.parent.mkdir(parents=True, exist_ok=True)
        if go:
            flag.write_text("1\n")
        elif flag.exists():
            flag.unlink()
        payload = {"tool_input": {"command": cmd}, "cwd": str(cwd), "session_id": "s"}
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        try:
            guard.main()
            return 0, ""
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            return code, capsys.readouterr().err

    return _run


def make_task(repo, name="01-x.py", md=True):
    d = repo / ".solve" / "tasks" / "t"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text("print(1)\n")
    if md:
        (d / "task.md").write_text("# task\n")
    return f".solve/tasks/t/{name}"


ALLOWED = [
    "grep x foo",
    "rg pattern",
    "find . -name '*.py'",
    "ls -la",
    "cat foo",
    "head -n5 foo",
    "awk '{print $1}' foo",
    "git diff",
    "git status",
    "git log --oneline",
    "git show HEAD",
    "cd /tmp",
    "grep x foo | head",
    "for f in a b; do grep x $f; done",
    "git init",
    "git -C .solve/tasks/t add -A",
    "git -C .solve/tasks/t commit -m scratch",
]

BLOCKED = [
    "git commit -m msg",
    "git add .",
    "git checkout main",
    "git reset --hard",
    "git stash",
    'python -c "print(1)"',
    'ruby -e "puts 1"',
    "grep x foo > out.txt",
    "find . -delete",
    "find . -exec rm {} ;",
    "rm foo",
    "npm install",
    "make",
    "sed -i s/a/b/ foo",
]


@pytest.mark.parametrize("cmd", ALLOWED)
def test_allowed(cmd, repo, run):
    code, err = run(cmd, repo)
    assert code == 0, f"{cmd!r} should be allowed, got {err!r}"


@pytest.mark.parametrize("cmd", BLOCKED)
def test_blocked(cmd, repo, run):
    code, err = run(cmd, repo)
    assert code == 2, f"{cmd!r} should be blocked"
    assert err


def test_task_script_runs(repo, run):
    path = make_task(repo)
    assert run(f"python {path}", repo)[0] == 0


def test_task_script_missing_file(repo, run):
    (repo / ".solve" / "tasks" / "t").mkdir(parents=True)
    (repo / ".solve" / "tasks" / "t" / "task.md").write_text("# t\n")
    code, err = run("python .solve/tasks/t/nope.py", repo)
    assert code == 2 and "does not exist" in err


def test_task_script_runs_without_md(repo, run):
    path = make_task(repo, md=False)
    assert run(f"python {path}", repo)[0] == 0


def test_args_after_script_blocked(repo, run):
    path = make_task(repo)
    code, err = run(f"python {path} --flag", repo)
    assert code == 2 and "last" in err


def test_rm_on_task_path_blocked(repo, run):
    path = make_task(repo)
    assert run(f"rm {path}", repo)[0] == 2


def test_allowlisted_passes(repo, run):
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(npm run build:*)"]}})
    )
    assert run("npm run build", repo)[0] == 0
    assert run("npm run build --prod", repo)[0] == 0
    assert run("npm run buildx", repo)[0] == 2


def test_split_keeps_quoted_semicolon():
    assert guard.split_segments('grep "a;b" foo') == [["grep", "a;b", "foo"]]


def test_split_on_pipe_and_and():
    assert guard.split_segments("grep x foo | head && ls") == [
        ["grep", "x", "foo"],
        ["head"],
        ["ls"],
    ]


def test_allowlisted_matching():
    assert guard.allowlisted("npm test", ["npm test:*"])
    assert guard.allowlisted("npm test x", ["npm test:*"])
    assert not guard.allowlisted("npm testx", ["npm test:*"])
    assert guard.allowlisted("lsof", ["ls*"])
    assert guard.allowlisted("exact cmd", ["exact cmd"])
    assert not guard.allowlisted("exact cmdx", ["exact cmd"])


def test_task_script_run_without_a_go_is_denied(repo, run):
    script = make_task(repo)
    code, err = run(f"python {script}", repo, go=False)
    assert code == 2 and "no go" in err


def test_search_without_a_go_stays_free(repo, run):
    assert run("grep x foo", repo, go=False)[0] == 0


def test_script_written_this_turn_runs(repo, run):
    """The gate is the sketch, not the write: the human read the script in chat
    before the go, so writing and running it land in the same turn."""
    script = make_task(repo)
    fresh = time.time() + 5
    os.utime(repo / script, (fresh, fresh))
    assert run(f"python {script}", repo)[0] == 0


def test_current_script_written_this_turn_runs(repo, run):
    script = make_task(repo, name="current.rb")
    fresh = time.time() + 5
    os.utime(repo / script, (fresh, fresh))
    assert run(f"ruby {script}", repo)[0] == 0


def test_script_from_an_earlier_turn_runs(repo, run):
    script = make_task(repo)
    old = time.time() - 60
    os.utime(repo / script, (old, old))
    assert run(f"python {script}", repo)[0] == 0
