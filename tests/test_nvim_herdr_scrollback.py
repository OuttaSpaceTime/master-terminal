import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

NVIM_CONFIG = Path.home() / ".config" / "nvim"

PROBE_LUA = """
vim.api.nvim_exec_autocmds("User", { pattern = "VeryLazy" })
vim.cmd.edit(vim.env.PROBE_FILE)
vim.fn.writefile({ tostring(vim.api.nvim_win_get_cursor(0)[1]) }, vim.env.PROBE_OUT)
"""

LINES = 200


def cursor_line_after_opening(filename):
    if not shutil.which("nvim"):
        pytest.skip("nvim not installed")
    if not NVIM_CONFIG.is_dir():
        pytest.skip("nvim config not deployed; run `chezmoi -S home apply`")
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "probe.lua"
        probe.write_text(PROBE_LUA)
        target = Path(tmp) / filename
        target.write_text("".join(f"line {n}\n" for n in range(1, LINES + 1)))
        out = Path(tmp) / "cursor.txt"
        subprocess.run(
            ["nvim", "--headless", "-c", f"luafile {probe}", "-c", "qa!"],
            env={**os.environ, "PROBE_FILE": str(target), "PROBE_OUT": str(out)},
            cwd=tmp,
            capture_output=True,
            timeout=120,
            check=True,
        )
        return int(out.read_text())


def test_herdr_scrollback_file_opens_on_its_last_line():
    assert cursor_line_after_opening("herdr-scrollback-1-2-0.txt") == LINES


def test_other_text_files_still_open_on_the_first_line():
    assert cursor_line_after_opening("notes.txt") == 1
