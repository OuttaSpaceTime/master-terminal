import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TAB_BAR = ROOT / "home/private_dot_config/kitty/tab_bar.py"

DRIVER = """
import json, runpy, sys
from types import SimpleNamespace
from kitty.fast_data_types import Color, Screen
from kitty.tab_bar import DrawData, ExtraData, TabBarData, as_rgb, draw_tab_with_fade

style, title, columns, tab_bar, cwd, name = sys.argv[1], sys.argv[2], int(sys.argv[3]), *sys.argv[4:]
if style == "custom":
    draw_tab = runpy.run_path(tab_bar)["draw_tab"]
    kitty_tab = SimpleNamespace(name=name, get_cwd_of_active_window=lambda: cwd)
    draw_tab.__globals__["get_boss"] = lambda: SimpleNamespace(tab_for_id=lambda tab_id: kitty_tab)
else:
    draw_tab = draw_tab_with_fade
gray = Color(0xe2, 0xe4, 0xea)
draw_data = DrawData(
    leading_spaces=0, sep="", trailing_spaces=0, bell_on_tab="", alpha=(0.25, 0.5, 0.75, 1),
    active_fg=Color(0x11, 0x13, 0x1a), active_bg=Color(0x74, 0xc7, 0xec),
    inactive_fg=Color(0x6c, 0x6f, 0x85), inactive_bg=gray, default_bg=gray,
    title_template="{title}", active_title_template=None, tab_activity_symbol="",
    powerline_style="angled", tab_bar_edge=1, max_tab_title_length=0,
    max_tab_title_lines=2, wrap_width=0, os_window_id=0,
)
screen = Screen(None, 4, columns)
screen.cursor.bg = as_rgb(0x74c7ec)
draw_tab(draw_data, screen, TabBarData(title=title), 0, columns, 1, True, ExtraData())
print(json.dumps({
    "rows": [str(screen.line(y)) for y in range(3)],
    "ansi": screen.line(0).as_ansi(),
    "cursor_y": screen.cursor.y,
    "bg_after": screen.cursor.bg,
    "bold": [screen.line(y).cursor_from(4).bold for y in range(2)],
}))
"""


@pytest.fixture
def draw(tmp_path):
    driver = tmp_path / "driver.py"
    driver.write_text(DRIVER)

    def run(title, columns=30, style="custom", cwd="", name=""):
        out = subprocess.run(
            ["kitty", "+launch", str(driver), style, title, str(columns), str(TAB_BAR), str(cwd), name],
            capture_output=True,
            text=True,
        )
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout)

    return run


def git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True)


def test_agent_tab_shows_repo_then_branch_state_and_agent(draw):
    tab = draw("C vilocify-portal/1123-keyset ⚙")
    assert tab["rows"] == [" ● vilocify-portal", "   1123-keyset · working · C", ""]
    assert tab["cursor_y"] == 1


def test_title_without_branch_shows_only_state_and_agent(draw):
    assert draw("O notes ✔")["rows"] == [" ● notes", "   done · O", ""]


def test_agent_tab_on_main_shows_main(draw):
    assert draw("C shop/main ✔")["rows"][1] == "   main · done · C"


def test_agent_tab_strips_the_branch_prefix(draw):
    assert draw("C shop/feature/login ⚙")["rows"][1] == "   login · working · C"


def test_branch_keeps_its_slashes(draw):
    assert draw("C shop/felix/x ⚙")["rows"][1] == "   felix/x · working · C"


@pytest.mark.parametrize(
    "mark, state, rgb",
    [
        ("⚙", "working", "224:97:0"),
        ("💭", "working", "224:97:0"),
        ("🧹", "working", "224:97:0"),
        ("✔", "done", "13:160:77"),
        ("🌱", "idle", "108:111:133"),
    ],
)
def test_marker_sets_state_word_and_dot_color(draw, mark, state, rgb):
    tab = draw(f"C shop {mark}")
    assert tab["rows"][1] == f"   {state} · C"
    assert f"38:2:{rgb}" in tab["ansi"].split("●")[0]


def test_long_lines_are_cut_with_an_ellipsis_instead_of_wrapping(draw):
    tab = draw("C vilocify-portal/1123-keyset ⚙", columns=20)
    assert tab["rows"] == [" ● vilocify-portal", "   1123-keyset · wo…", ""]


def test_blocked_tab_shows_a_question_mark_and_a_bold_needs_you_row(draw):
    tab = draw("C vilocify-portal/1123-keyset ❓")
    assert tab["rows"] == ["❓ vilocify-portal", "   1123-keyset · needs you · C", ""]
    assert tab["bold"] == [False, True]


def test_blocked_tab_counts_the_wide_question_mark_when_cutting(draw):
    assert draw("C vilocify-portal/x ❓", columns=16)["rows"][0] == "❓ vilocify-por…"


def test_tab_background_does_not_leak_into_the_rest_of_the_sidebar(draw):
    assert draw("C shop ✔")["bg_after"] == 0


@pytest.mark.parametrize("title", ["zsh", "codex shop ✔", "C shop"])
def test_other_titles_are_drawn_like_the_fade_style(draw, title):
    assert draw(title)["rows"] == draw(title, style="fade")["rows"]


@pytest.mark.parametrize("title", ["zsh", "nvim ~/notes"])
def test_shell_tab_outside_git_is_drawn_like_the_fade_style(draw, tmp_path, title):
    assert draw(title, cwd=tmp_path)["rows"] == draw(title, style="fade")["rows"]


def test_shell_tab_in_a_repo_shows_repo_and_branch(draw, tmp_path):
    repo = tmp_path / "shop"
    git("init", "-q", "-b", "feature/login", str(repo))
    (repo / "app").mkdir()
    assert draw("zsh", cwd=repo / "app")["rows"] == [" ● shop", "   login", ""]


def test_shell_tab_on_main_shows_main(draw, tmp_path):
    repo = tmp_path / "shop"
    git("init", "-q", "-b", "main", str(repo))
    tab = draw("nvim ~/shop", cwd=repo)
    assert tab["rows"] == [" ● shop", "   main", ""]
    assert "38:2:158:75:236" in tab["ansi"].split("●")[0]


def test_shell_tab_in_a_worktree_names_the_main_repository(draw, tmp_path):
    repo = tmp_path / "vilocify-portal"
    git("init", "-q", "-b", "main", str(repo))
    git("-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")
    wt = tmp_path / "worktrees" / "1123-keyset-6-eol-coalesce-sort"
    git("-C", str(repo), "worktree", "add", "-q", "-b", "1123-keyset-6-eol-coalesce-sort", str(wt))
    assert draw("zsh", cwd=wt, columns=40)["rows"] == [" ● vilocify-portal", "   1123-keyset-6-eol-coalesce-sort", ""]
    assert draw("zsh", cwd=wt, columns=20)["rows"] == [" ● vilocify-portal", "   1123-keyset-6-eo…", ""]


def test_named_tab_keeps_its_name_inside_a_repo(draw, tmp_path):
    repo = tmp_path / "shop"
    git("init", "-q", "-b", "main", str(repo))
    assert draw("logs", cwd=repo, name="logs")["rows"] == draw("logs", style="fade")["rows"]


def test_shell_tab_background_does_not_leak_into_the_rest_of_the_sidebar(draw, tmp_path):
    repo = tmp_path / "shop"
    git("init", "-q", "-b", "main", str(repo))
    assert draw("zsh", cwd=repo)["bg_after"] == 0
