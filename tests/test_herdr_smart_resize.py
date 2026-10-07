import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "home/private_dot_config/herdr/smart-resize/scripts/herdr-resize.sh"


def run_resize(tmp_path, direction, foreground):
    log = tmp_path / "calls.log"
    process_info = {"result": {"process_info": {"foreground_processes": [{"name": foreground}]}}}
    fake_herdr = tmp_path / "herdr"
    fake_herdr.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> {log}\n'
        f"[ \"$1 $2\" = 'pane process-info' ] && echo '{json.dumps(process_info)}'\n"
        "exit 0\n"
    )
    fake_herdr.chmod(0o755)
    subprocess.run(
        ["bash", str(SCRIPT), direction],
        env={"PATH": "/usr/bin:/bin", "HERDR_BIN_PATH": str(fake_herdr), "HERDR_PANE_ID": "p1"},
        check=True,
    )
    return log.read_text().splitlines()[1:]


def test_nvim_pane_gets_the_alt_key(tmp_path):
    assert run_resize(tmp_path, "left", "nvim") == ["pane send-keys p1 alt+h"]


def test_other_pane_resizes_the_herdr_split(tmp_path):
    assert run_resize(tmp_path, "right", "zsh") == ["pane resize --direction right --current"]
