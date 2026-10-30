import subprocess
from pathlib import Path

import pytest

ALIASES = Path.home() / "Code/Misc/agentic-setup/shell/aliases.zsh"


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path):
    main = tmp_path / "main"
    git("init", "-q", "-b", "main", str(main))
    git("-C", str(main), "commit", "-q", "--allow-empty", "-m", "init")
    for name in ("wt1", "wt2"):
        git("-C", str(main), "worktree", "add", "-q", str(tmp_path / name))
    (tmp_path / "wt1/sub").mkdir()
    return tmp_path


def gwr(cwd, pick):
    # The database sweep only runs for ~/Code/Vilocify/vilocify-portal, so it never runs here.
    script = f"""
eval "$(sed -n '/^gwr() {{/,/^}}/p' {ALIASES})"
fzf() {{ grep -E "^({pick})\t" }}
cd {cwd}
gwr
print -r -- "$PWD"
"""
    out = subprocess.run(["zsh", "-f", "-c", script], capture_output=True, text=True)
    return out.stderr, Path(out.stdout.strip())


def worktrees(repo):
    return [Path(line.split()[0]).name for line in git("-C", str(repo / "main"), "worktree", "list").splitlines()]


def test_removing_the_worktree_you_stand_in_moves_you_to_main(repo):
    stderr, pwd = gwr(repo / "wt1", "wt1")
    assert "fatal" not in stderr
    assert pwd == repo / "main"
    assert worktrees(repo) == ["main", "wt2"]


def test_removing_from_a_subdirectory_moves_you_to_main(repo):
    stderr, pwd = gwr(repo / "wt1/sub", "wt1")
    assert "fatal" not in stderr
    assert pwd == repo / "main"


def test_removes_every_picked_worktree_when_one_is_current(repo):
    stderr, pwd = gwr(repo / "wt1", "wt1|wt2")
    assert "fatal" not in stderr
    assert worktrees(repo) == ["main"]


def test_removing_another_worktree_keeps_you_in_place(repo):
    stderr, pwd = gwr(repo / "wt2", "wt1")
    assert "fatal" not in stderr
    assert pwd == repo / "wt2"
    assert worktrees(repo) == ["main", "wt2"]
