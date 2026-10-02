import json
import os
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "home/dot_local/bin/executable_kitty-agent-title"
PLUGIN = ROOT / "home/private_dot_config/opencode/plugins/kitty-agent-title.js"


def git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True)


@pytest.fixture
def env(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    kitten = bin_dir / "kitten"
    kitten.write_text(f'#!/bin/sh\nprintf "%s|" "$@" >> {tmp_path}/kitten.log\necho >> {tmp_path}/kitten.log\n')
    kitten.chmod(0o755)
    runtime = tmp_path / "run"
    runtime.mkdir()
    e = dict(os.environ)
    e.pop("HERDR_ENV", None)
    e.update(PATH=f"{bin_dir}:{e['PATH']}", KITTY_WINDOW_ID="99", XDG_RUNTIME_DIR=str(runtime))
    return e


def title(env, tmp_path, agent, event, cwd, tool=""):
    out = subprocess.run(
        ["bash", str(SCRIPT), agent],
        input=json.dumps({"hook_event_name": event, "cwd": str(cwd), "tool_name": tool}),
        capture_output=True,
        text=True,
        env=env,
    )
    assert out.returncode == 0
    assert out.stdout == ""
    log = tmp_path / "kitten.log"
    return log.read_text().splitlines() if log.exists() else []


def test_branch_and_state_in_title(env, tmp_path):
    repo = tmp_path / "shop"
    git("init", "-q", "-b", "feature/login", str(repo))
    assert title(env, tmp_path, "claude", "PreToolUse", repo) == ["@|set-tab-title|C shop/feature/login ⚙|"]


def test_question_to_the_user_counts_as_needs_you(env, tmp_path):
    repo = tmp_path / "shop"
    git("init", "-q", "-b", "main", str(repo))
    assert title(env, tmp_path, "claude", "PreToolUse", repo, tool="AskUserQuestion") == ["@|set-tab-title|C shop/main ❓|"]


def test_main_branch_is_kept(env, tmp_path):
    repo = tmp_path / "shop"
    git("init", "-q", "-b", "main", str(repo))
    assert title(env, tmp_path, "claude", "Stop", repo) == ["@|set-tab-title|C shop/main ✔|"]


def test_worktree_shows_the_main_repository_name(env, tmp_path):
    repo = tmp_path / "vilocify-portal"
    git("init", "-q", "-b", "main", str(repo))
    git("-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")
    wt = tmp_path / "worktrees" / "1123-keyset"
    git("-C", str(repo), "worktree", "add", "-q", "-b", "1123-keyset", str(wt))
    assert title(env, tmp_path, "claude", "PermissionRequest", wt) == ["@|set-tab-title|C vilocify-portal/1123-keyset ❓|"]


def test_opencode_label_outside_git(env, tmp_path):
    plain = tmp_path / "notes"
    plain.mkdir()
    assert title(env, tmp_path, "opencode", "SessionStart", plain) == ["@|set-tab-title|O notes 🌱|"]


def test_marker_records_the_window_for_the_shell_reset(env, tmp_path):
    title(env, tmp_path, "claude", "UserPromptSubmit", tmp_path)
    assert (tmp_path / "run" / "kitty-agent-title.99").exists()


def test_skipped_inside_herdr(env, tmp_path):
    env["HERDR_ENV"] = "1"
    assert title(env, tmp_path, "claude", "Stop", tmp_path) == []
    assert not (tmp_path / "run" / "kitty-agent-title.99").exists()


def reset_in_zsh(env, tmp_path):
    zshrc = (ROOT / "home/dot_zshrc").read_text()
    func = zshrc[zshrc.index("reset-kitty-agent-title() {"):]
    func = func[: func.index("\n}\n") + 3]
    subprocess.run(["zsh", "-f", "-c", func + "reset-kitty-agent-title"], check=True, env=env)
    log = tmp_path / "kitten.log"
    return log.read_text().splitlines() if log.exists() else []


def test_shell_reset_clears_the_title_once_after_the_agent(env, tmp_path):
    marker = tmp_path / "run" / "kitty-agent-title.99"
    marker.touch()
    assert reset_in_zsh(env, tmp_path) == ["@|set-tab-title||"]
    assert not marker.exists()
    assert reset_in_zsh(env, tmp_path) == ["@|set-tab-title||"]


def test_shell_reset_leaves_other_windows_alone(env, tmp_path):
    (tmp_path / "run" / "kitty-agent-title.7").touch()
    assert reset_in_zsh(env, tmp_path) == []


def test_opencode_plugin_maps_events_to_hook_names(tmp_path):
    home = tmp_path / "home"
    (home / ".local/bin").mkdir(parents=True)
    fake = home / ".local/bin/kitty-agent-title"
    fake.write_text(f'#!/bin/sh\nprintf "%s %s\\n" "$1" "$(cat)" >> {tmp_path}/calls.log\n')
    fake.chmod(0o755)
    driver = f"""
const {{ KittyAgentTitle }} = await import({json.dumps(PLUGIN.as_uri())});
const hooks = await KittyAgentTitle({{ directory: "/w" }});
await hooks["chat.message"]({{}}, {{}});
await hooks["tool.execute.before"]({{ tool: "bash" }}, {{ args: {{}} }});
await hooks["tool.execute.after"]({{ tool: "bash" }}, {{}});
for (const type of ["permission.asked", "question.asked", "session.idle", "session.compacted", "message.updated"]) {{
  await hooks.event({{ event: {{ type, properties: {{}} }} }});
}}
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", driver],
        check=True,
        env={**os.environ, "HOME": str(home)},
    )
    log = tmp_path / "calls.log"
    for _ in range(50):
        if log.exists() and len(log.read_text().splitlines()) >= 8:
            break
        time.sleep(0.05)
    calls = sorted(log.read_text().splitlines())
    events = ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse",
              "PermissionRequest", "PermissionRequest", "Stop", "PreCompact"]
    assert calls == sorted(f'opencode {{"hook_event_name":"{e}","cwd":"/w"}}' for e in events)
