import collections
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "home/dot_claude/modify_settings.json"


def run(live):
    out = subprocess.run(
        ["python3", str(SCRIPT)], input=live, capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout, object_pairs_hook=collections.OrderedDict)


def test_live_wins_for_keys_toggled_in_the_ui():
    assert run('{"effortLevel": "xhigh", "theme": "dark"}')["effortLevel"] == "xhigh"


def test_repo_default_fills_in_a_ui_key_the_live_file_lacks():
    assert run("{}")["effortLevel"] == "high"


def test_repo_wins_for_structural_keys():
    got = run('{"hooks": {"Stop": []}, "statusLine": {"type": "tampered"}}')
    assert got["statusLine"]["command"].endswith("statusline-script.sh")
    assert "PreToolUse" in got["hooks"]


def test_repo_hides_commit_and_pr_attribution():
    got = run('{"attribution": {"commit": "Co-Authored-By: Claude"}}')
    assert got["attribution"] == {"commit": "", "pr": ""}


def test_empty_stdin_produces_a_complete_settings_file():
    got = run("")
    for key in ("$schema", "permissions", "hooks", "statusLine", "model", "outputStyle"):
        assert key in got


def test_live_key_order_is_preserved():
    live = '{"theme": "dark", "verbose": true, "model": "opus"}'
    assert list(run(live))[:3] == ["theme", "verbose", "model"]


def test_unknown_live_keys_survive():
    assert run('{"someNewSetting": 42}')["someNewSetting"] == 42


def test_output_is_stable_when_fed_its_own_output():
    once = subprocess.run(
        ["python3", str(SCRIPT)], input="{}", capture_output=True, text=True, check=True
    ).stdout
    twice = subprocess.run(
        ["python3", str(SCRIPT)], input=once, capture_output=True, text=True, check=True
    ).stdout
    assert once == twice
