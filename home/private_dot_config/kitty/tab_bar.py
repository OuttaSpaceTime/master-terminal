import re
from pathlib import Path

from kitty.fast_data_types import get_boss
from kitty.tab_bar import as_rgb, draw_tab_with_fade

AGENT_TITLE = re.compile(r"(?P<agent>[CO]) (?P<repo>[^/ ]+)(?:/(?P<branch>\S+))? (?P<mark>❓|⚙|💭|🧹|✔|🌱)")

STATES = {
    "❓": ("blocked", 0xFA0032),
    "⚙": ("working", 0xE06100),
    "💭": ("working", 0xE06100),
    "🧹": ("working", 0xE06100),
    "✔": ("done", 0x0DA04D),
    "🌱": ("idle", 0x6C6F85),
}


def fit(text, width):
    return text if len(text) <= width else text[: width - 1] + "…"


def repo_and_branch(cwd):
    if not cwd:
        return None
    for folder in (Path(cwd), *Path(cwd).parents):
        dot_git = folder / ".git"
        if dot_git.is_dir():
            git_dir = dot_git
            break
        if dot_git.is_file():
            git_dir = folder / dot_git.read_text().removeprefix("gitdir: ").strip()
            break
    else:
        return None

    commondir = git_dir / "commondir"
    common_dir = (git_dir / commondir.read_text().strip()).resolve() if commondir.exists() else git_dir
    head = (git_dir / "HEAD").read_text().strip()
    branch = head.removeprefix("ref: refs/heads/") if head.startswith("ref: refs/heads/") else ""
    return common_dir.parent.name, branch


def short_branch(branch):
    if branch.startswith(("feature/", "fix/", "bugfix/", "chore/")):
        return branch.split("/", 1)[1]
    return branch


def draw_tab(draw_data, screen, tab, before, max_tab_length, index, is_last, extra_data):
    match = AGENT_TITLE.fullmatch(tab.title)
    if match:
        state, color = STATES[match["mark"]]
        repo = match["repo"]
        details = " · ".join([short_branch(match["branch"]), state, match["agent"]] if match["branch"] else [state, match["agent"]])
    else:
        kitty_tab = get_boss().tab_for_id(tab.tab_id)
        cwd = kitty_tab and not kitty_tab.name and kitty_tab.get_cwd_of_active_window()
        label = repo_and_branch(cwd)
        if label is None:
            return draw_tab_with_fade(draw_data, screen, tab, before, max_tab_length, index, is_last, extra_data)
        color = 0x9E4BEC
        repo, branch = label
        details = short_branch(branch)

    fg = screen.cursor.fg
    screen.draw(" ")
    screen.cursor.fg = as_rgb(color)
    screen.draw("●")
    screen.cursor.fg = fg
    screen.draw(fit(" " + repo, screen.columns - 2))
    if details:
        screen.cursor.x = 0
        screen.cursor.y += 1
        screen.draw(fit("   " + details, screen.columns))
    screen.cursor.bg = 0
    return screen.cursor.x
