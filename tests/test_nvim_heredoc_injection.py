import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
NVIM_CONFIG = Path.home() / ".config" / "nvim"

PROBE_LUA = """
vim.cmd.edit(vim.env.PROBE_FILE)
local buf = vim.api.nvim_get_current_buf()
vim.treesitter.start(buf)
vim.treesitter.get_parser(buf):parse(true)
local langs = {}
for row = 0, vim.api.nvim_buf_line_count(buf) - 1 do
  local line = vim.api.nvim_buf_get_lines(buf, row, row + 1, false)[1]
  for _, capture in ipairs(vim.treesitter.get_captures_at_pos(buf, row, #line:match('^%s*'))) do
    langs[capture.lang] = true
  end
end
vim.fn.writefile(vim.tbl_keys(langs), vim.env.PROBE_OUT)
"""


def capture_languages(ruby_source):
    if not shutil.which("nvim"):
        pytest.skip("nvim not installed")
    if not NVIM_CONFIG.is_dir():
        pytest.skip("nvim config not deployed; run `chezmoi -S home apply`")
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "probe.lua"
        probe.write_text(PROBE_LUA)
        ruby = Path(tmp) / "probe.rb"
        ruby.write_text(ruby_source)
        out = Path(tmp) / "langs.txt"
        subprocess.run(
            ["nvim", "--headless", "-c", f"luafile {probe}", "-c", "qa!"],
            env={**os.environ, "PROBE_FILE": str(ruby), "PROBE_OUT": str(out)},
            cwd=tmp,
            capture_output=True,
            timeout=120,
            check=True,
        )
        return set(out.read_text().split())


def test_sql_heredoc_is_highlighted_as_sql():
    langs = capture_languages(
        "rows = connection.select_all(<<~SQL)\n"
        "  SELECT id, name FROM users WHERE created_at > NOW()\n"
        "SQL\n"
    )
    assert "sql" in langs


def test_js_heredoc_is_highlighted_as_javascript():
    langs = capture_languages(
        "script = <<~JS\n"
        "  const total = 1;\n"
        "JS\n"
    )
    assert "javascript" in langs
