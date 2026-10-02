import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "home" / "private_dot_config" / "nvim" / "lua" / "plugins" / "diffview.lua"
LAZY = Path.home() / ".local" / "share" / "nvim" / "lazy"

PROBE_LUA = """
local spec = dofile(vim.env.SPEC)[1]
local keys = {}
for _, key in ipairs(spec.keys) do keys[key[1]] = key[2] end
local setup = spec.config or function(_, opts) require("diffview").setup(opts) end
setup(nil, spec.opts)

vim.cmd("DiffviewOpen")
local view
vim.wait(5000, function()
  view = require("diffview.lib").get_current_view()
  return view and #view.panel.files.working == 3
end)
vim.cmd("DiffviewFocusFiles")

local function label(row)
  local comp = view.panel.components.comp:get_comp_on_line(row + 1)
  if comp and comp.name == "file" then return comp.context.path end
  if comp and comp.name == "dir_name" then return comp.parent.context.name .. "/" end
end

local function visible()
  local labels = {}
  for row = 0, vim.api.nvim_buf_line_count(view.panel.bufid) - 1 do
    labels[#labels + 1] = label(row)
  end
  return labels
end

local function marked()
  local ns = vim.api.nvim_get_namespaces()["diffview_viewed"]
  local labels = {}
  for _, mark in ipairs(vim.api.nvim_buf_get_extmarks(view.panel.bufid, ns, 0, -1, {})) do
    labels[#labels + 1] = label(mark[2]) or ("row " .. mark[2])
  end
  return labels
end

local function cursor_to(wanted)
  for row = 0, vim.api.nvim_buf_line_count(view.panel.bufid) - 1 do
    if label(row) == wanted then
      vim.api.nvim_win_set_cursor(view.panel.winid, { row + 1, 0 })
      return
    end
  end
  error("no panel row for " .. wanted)
end

local function mark(path)
  cursor_to(path)
  keys["<leader>Dv"]()
end

local function collapse(dir)
  cursor_to(dir)
  require("diffview.actions").toggle_fold()
end

local scenarios = {
  all_marked_folder_collapsed = function()
    mark("a/x.txt")
    mark("a/y.txt")
    collapse("a/")
    return marked()
  end,
  partly_marked_folder_collapsed = function()
    mark("a/x.txt")
    collapse("a/")
    return marked()
  end,
  marks_after_next_file_from_diff_window = function()
    mark("a/x.txt")
    mark("a/y.txt")
    vim.cmd("wincmd l")
    view:next_file()
    return marked()
  end,
  filter_cycle = function()
    mark("a/x.txt")
    mark("a/y.txt")
    local states = { visible() }
    for _ = 1, 3 do
      keys["<leader>Dm"]()
      states[#states + 1] = visible()
    end
    return states
  end,
  marking_under_unviewed_filter_hides_file = function()
    keys["<leader>Dm"]()
    mark("b.txt")
    return visible()
  end,
}

vim.fn.writefile({ vim.json.encode(scenarios[vim.env.SCENARIO]()) }, vim.env.PROBE_OUT)
vim.cmd("qa!")
"""


def run_scenario(scenario):
    if not shutil.which("nvim"):
        pytest.skip("nvim not installed")
    if not (LAZY / "diffview.nvim").is_dir():
        pytest.skip("diffview.nvim not installed by lazy.nvim")
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        (repo / "a").mkdir(parents=True)
        for name in ["a/x.txt", "a/y.txt", "b.txt"]:
            (repo / name).write_text("one\n")
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run([*git, "commit", "-q", "-m", "init"], cwd=repo, check=True)
        for name in ["a/x.txt", "a/y.txt", "b.txt"]:
            (repo / name).write_text("one\ntwo\n")

        probe = Path(tmp) / "probe.lua"
        probe.write_text(PROBE_LUA)
        out = Path(tmp) / "out.json"
        result = subprocess.run(
            [
                "nvim", "--headless", "--clean",
                "--cmd", f"set rtp+={LAZY / 'diffview.nvim'},{LAZY / 'nvim-web-devicons'}",
                "-c", f"luafile {probe}",
                "-c", "cq",
            ],
            env={
                **os.environ,
                "XDG_STATE_HOME": str(Path(tmp) / "state"),
                "SPEC": str(SPEC),
                "SCENARIO": scenario,
                "PROBE_OUT": str(out),
            },
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert out.exists(), result.stderr
        return json.loads(out.read_text())


def test_collapsed_folder_with_all_files_viewed_carries_the_mark():
    assert run_scenario("all_marked_folder_collapsed") == ["a/"]


def test_collapsed_folder_with_some_files_viewed_shows_no_mark():
    assert run_scenario("partly_marked_folder_collapsed") == []


def test_marks_survive_moving_to_the_next_file_from_the_diff_window():
    assert run_scenario("marks_after_next_file_from_diff_window") == ["a/x.txt", "a/y.txt"]


def test_filter_cycles_all_then_unviewed_then_viewed_then_all():
    everything = ["a/", "a/x.txt", "a/y.txt", "b.txt"]
    assert run_scenario("filter_cycle") == [
        everything,
        ["b.txt"],
        ["a/", "a/x.txt", "a/y.txt"],
        everything,
    ]


def test_marking_a_file_under_the_unviewed_filter_hides_it():
    assert run_scenario("marking_under_unviewed_filter_hides_file") == ["a/", "a/x.txt", "a/y.txt"]
