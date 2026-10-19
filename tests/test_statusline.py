import json
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "home/dot_claude/statusline-script.sh"

GREEN = "\033[1;38;2;13;160;77m"
YELLOW = "\033[1;38;2;224;97;0m"


def render(cwd, off, **extra):
    payload = {
        "session_id": "test-statusline",
        "workspace": {"current_dir": str(cwd)},
        "model": {"id": "claude-opus-5[1m]"},
        "effort": {"level": "high"},
        "context_window": {"used_percentage": 10, "context_window_size": 1000000},
        **extra,
    }
    env = {"PATH": os.environ["PATH"], "HOME": os.environ["HOME"]}
    if off:
        env["SOLVEIT_OFF"] = "1"
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.stdout


def test_solveit_on_shows_green_solve_badge(tmp_path):
    assert render(tmp_path, off=False).startswith(f"{GREEN}solve")


def test_solveit_off_shows_orange_free_badge(tmp_path):
    assert render(tmp_path, off=True).startswith(f"{YELLOW}free")


def test_badge_precedes_the_model_tier(tmp_path):
    out = render(tmp_path, off=True)
    assert out.index("free") < out.index("Opus")


def assistant_line(msg_id, **usage):
    return json.dumps({"type": "assistant", "message": {"id": msg_id, "usage": usage}})


def test_shows_session_cost_in_dollars(tmp_path):
    out = render(tmp_path, off=True, cost={"total_cost_usd": 0.14325975})
    assert "$0.14" in out


def test_sums_session_tokens_counting_each_message_once(tmp_path):
    transcript = tmp_path / "session.jsonl"
    split_message = assistant_line(
        "msg_a",
        input_tokens=2,
        cache_creation_input_tokens=400000,
        cache_read_input_tokens=500000,
        output_tokens=98,
    )
    transcript.write_text("\n".join([
        json.dumps({"type": "user", "message": {"content": "hi"}}),
        split_message,
        split_message,
        assistant_line("msg_b", input_tokens=0, cache_read_input_tokens=300000, output_tokens=0),
    ]))
    out = render(tmp_path, off=True, transcript_path=str(transcript))
    assert "Σ1.2M" in out


def test_groups_are_separated_by_spaces_not_pipes(tmp_path):
    out = render(tmp_path, off=True, cost={"total_cost_usd": 1}, rate_limits={"five_hour": {"used_percentage": 12}})
    assert "|" not in out


def test_shows_branch_without_folder_name(tmp_path):
    repo = tmp_path / "some-project"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "trunk", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init"],
        check=True,
    )
    out = render(repo, off=True)
    assert "trunk" in out
    assert "some-project" not in out
