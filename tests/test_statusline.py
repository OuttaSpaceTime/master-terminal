import json
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "home/dot_claude/statusline-script.sh"

GREEN = "\033[1;38;2;13;160;77m"
YELLOW = "\033[1;38;2;224;97;0m"


def render(cwd, off):
    payload = {
        "session_id": "test-statusline",
        "workspace": {"current_dir": str(cwd)},
        "model": {"id": "claude-opus-5[1m]"},
        "effort": {"level": "high"},
        "context_window": {"used_percentage": 10, "context_window_size": 1000000},
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
