---
title: Kitty
tags: [kitty, terminal]
created: 2026-04-07
updated: 2026-10-01
---

# Kitty

## Update

- This machine uses the official binary install: `kitty 0.49.2` at `~/.local/kitty.app`
- Update it by re-running the installer. `launch=n` stops it from opening a new kitty when done:

```bash
curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin launch=n
```

- The installer deletes and replaces `~/.local/kitty.app`, so restart kitty afterwards. The running instance may lazily load modules from the new version.
- Kitty’s own update check only applies to official binary builds; distro packages do not use it
- Kitty silently ignores bad option values (`tab_bar_edge sideways` falls back to the default) and logs unknown keys as `Ignoring unknown config key`. Check a config against the installed version with `kitty +runpy "from kitty.config import load_config; o = load_config('<path>'); print(o.tab_bar_edge)"`. `tab_bar_edge` comes out as a number: top 2, bottom 8, left 1, right 4.
- Renamed options: `tab_bar_drag_threshold` (≤ 0.46) became `drag_threshold` (0.47+), and a value of `0` now disables *all* tab and window dragging

## Shortcuts

- `Ctrl+Shift+T` — new window
- `Ctrl+Shift+Enter` — new split
- `Ctrl+Shift+,` — move the active tab left within the current kitty window
- `Ctrl+Shift+.` — move the active tab right within the current kitty window
- `Ctrl+Shift+[` / `Ctrl+Shift+]` — switch between splits
- `Ctrl+Shift+W` — close current split (or tab if only split)
- `Ctrl+Shift+F5` — reload kitty config
- `Ctrl+A` — jump to beginning of input line (readline/zsh)
- `Ctrl+E` — jump to end of input line (readline/zsh)
- `Ctrl+Alt+H` / `Ctrl+Alt+L` — previous / next tab
- `Ctrl+Alt+K` — clear the current terminal screen
- `Ctrl+Shift+Alt+T` — rename current tab
- `kitten @ set-tab-title "New Name"` — rename tab from CLI

## Moving / Swapping Windows (Splits)

Split *navigation* is remapped to `Ctrl+H/J/K/L` (`neighboring_window`), which works in every layout. Split *swapping* is layout-dependent:

- `Ctrl+Alt+Shift+H/J/K/L` — `move_window left/down/up/right`. **Directional swap only works in the `splits` layout** — it's a silent no-op in `fat`/`tall`/`grid`, which are auto-tiled (kitty owns geometry, no real left/right neighbor).
- `Alt+Shift+N` / `Alt+Shift+P` — `move_window_forward` / `_backward`. Non-directional; rotates the window through the position list, so it works in any layout (this is how you "cycle" in `grid`).

`enabled_layouts splits,fat,grid,horizontal,stack,tall,vertical` keeps every layout but makes `splits` the startup layout for new tabs (the first listed wins). Existing tabs keep their layout across a config reload; switch one live with `kitten @ goto-layout splits` (needs remote control, which is on). Reload config after edits with `Ctrl+Shift+F5`.

## Line Editing

These are the usual readline/zsh-style shortcuts for editing commands in the prompt:

- `Alt+F` — move forward one word
- `Alt+B` — move back one word
- `Ctrl+A` — jump to the start of the line
- `Ctrl+E` — jump to the end of the line
- `Alt+D` — delete the next word
- `Ctrl+W` — delete the previous word
- `Ctrl+R` — search shell history interactively

## Scrolling (Keyboard)

Kitty default scroll bindings use `kitty_mod` (`Ctrl+Shift` by default):

- `Ctrl+Shift+↑` / `Ctrl+Shift+↓` — scroll by line
- `Ctrl+Shift+PageUp` / `Ctrl+Shift+PageDown` — scroll by page
- `Shift+Alt+Up` / `Shift+Alt+Down` — scroll by half a page
- `Ctrl+Shift+Home` / `Ctrl+Shift+End` — scroll to top / bottom
- `Ctrl+Shift+Z` / `Ctrl+Shift+X` — jump to previous / next shell prompt (requires shell integration)

This repo also binds kitty-scrollback.nvim for vim-style browsing:

- `Ctrl+Shift+H` — open full scrollback buffer in nvim (`kitty.conf:78`)
- `Ctrl+Shift+G` — open last command's output in nvim (`kitty.conf:80`)
- Inside the nvim pager: normal motions (`j/k`, `Ctrl+U`/`Ctrl+D`, `gg`/`G`, `/` to search)

## Copy On Select

- `copy_on_select yes` copies selected text to the clipboard automatically
- `strip_trailing_spaces smart` strips trailing whitespace from copied selections so pasted commands don't carry extra line breaks from terminal line-wrapping
  - Values: `never` (default, keeps everything), `smart` (strip on normal selections, preserve in rectangle selections), `always` (strip on both)
  - Rectangle selection in kitty: hold `Ctrl+Alt` while dragging — selects a block instead of flowing line-by-line, useful for grabbing aligned columns where padding spaces matter
  - Stripping only affects the clipboard contents, not the visual highlight — the selection overlay still covers the whitespace
  - Only trailing whitespace (between the last non-space character and the newline) is removed; leading whitespace and inter-word spaces are preserved

## Sessions

- `F7` — save session (prompts for name, saves under `~/.local/share/kitty/sessions`)
- `F8` — restore/switch sessions (only shows files with recognized session extension)
- Plain names like `test` without the session extension won't appear in F8

## Tab Titles

- `kitty @ set-tab-title` is what the shell uses to rename the active tab
- The tab bar is a left sidebar: `tab_bar_edge left`, which needs kitty 0.48+ (0.47 accepts only top/bottom). Its width follows `tab_title_max_length` one cell per step (24 here; about 20 when unset). `tab_title_max_lines 2` is what lets a tab be two rows tall; `tab_title_wrap yes` only affects titles drawn by the `fade` fallback.
- `Ctrl+Alt+Shift+Right` / `Left` set the width to 35 / 20 via `remote_control load-config -o tab_title_max_length=N`. The last key pressed wins, each press reloads the whole config, and a restart goes back to the `kitty.conf` value.
- zsh sets no titles itself (`DISABLE_AUTO_TITLE="true"`)
- Agent tabs get titles with repo, raw branch and state, e.g. `C vilocify-portal/1123-keyset ❓` (`C` Claude, `O` opencode; 🌱 start, 💭 thinking, ⚙ tool, ❓ needs you, ✔ done, 🧹 compacting). Based on [flurdy's recipe](https://flurdy.com/docs/kitty-ai-tabs/):
  - `~/.local/bin/kitty-agent-title <agent>` reads hook JSON on stdin and runs `kitten @ set-tab-title`; in a worktree it names the main repo via `--git-common-dir`. It writes the branch unshortened (`main`, `feature/x`); the sidebar shortens it
  - Claude: hooks in the `MANAGED` blob of `home/dot_claude/modify_settings.json`; opencode: `home/private_dot_config/opencode/plugins/kitty-agent-title.js` pipes Claude-shaped JSON into the same script
  - The script touches `$XDG_RUNTIME_DIR/kitty-agent-title.$KITTY_WINDOW_ID`; the zsh `precmd` hook `reset-kitty-agent-title` clears the tab title only in that window, so a command in a sibling split doesn't wipe the agent's state
  - Skipped when `HERDR_ENV=1`: herdr panes inherit the herdr server's stale `KITTY_WINDOW_ID`
  - Tests: `tests/test_kitty_agent_title.py`
- `shell_integration enabled no-title` prevents kitty shell integration from changing titles based on the running foreground command
- `tab_title_template "{title}"` lets the tab bar show restored/manual tab titles from sessions instead of forcing a numeric index

### Sidebar (`tab_bar_style custom`)

`home/private_dot_config/kitty/tab_bar.py` draws herdr-style two-row entries; tests in `tests/test_kitty_tab_bar.py`.

- Agent title (`C|O repo[/branch] mark`): ` ● repo` / `   branch · state · agent`. Dot colour from the herdr palette: red blocked ❓, orange working ⚙💭🧹, green done ✔, grey idle 🌱
- Any other tab without an explicit name (`Tab.name` empty) whose active window's cwd is in git: mauve ` ● repo` / `   branch`. Worktrees show the main repo. The label follows `cd` without a tab switch
- Everything else (named tabs, no repo) is drawn by kitty's `draw_tab_with_fade`
- `short_branch` strips `feature/` `fix/` `bugfix/` `chore/` for both kinds; `main`/`master` are shown
- Repo/branch come from reading `.git`, `gitdir:`, `commondir` and `HEAD` directly, not `git`: two `git` calls take ~7 ms and kitty calls `draw_tab` twice per tab on every redraw, on its main thread

Gotchas (kitty 0.49.2, found by `dis`-ing its frozen Python via `kitty +launch probe.py`):

- The blank row between tabs is hard-coded (`TabBar.update_vertical`: `spacing = 1`, dropped only when the tabs don't fit). No option or `draw_tab` can remove it. It is painted with `tab_bar_background`, so that is set to the inactive-tab grey `#e2e4ea` to avoid white stripes
- `draw_tab` must end with `screen.cursor.bg = 0`: kitty paints the gaps and the empty area with whatever background the last drawn tab left set (the active tab's blue leaked when the last tab was active)
- `draw_tab` must cut rows to `screen.columns` itself (`fit`); kitty doesn't
- `tab_bar.py` is loaded once per kitty process and title rendering already tries at startup, so a kitty started before the file existed caches "no `draw_tab`". `Boss.load_config_file` applies options *before* `tab_bar.clear_caches`, so after creating or editing `tab_bar.py` run `kitten @ load-config` **twice**
- A `tab_bar.py` that fails to load makes kitty fall back to `fade` and log `Failed to load custom tab_bar.py`; kitty's stderr goes to the journal via gnome-shell's stream, not under kitty's PID

## Moving And Reordering Tabs

- Within the current kitty window, use `Ctrl+Shift+,` and `Ctrl+Shift+.` to move the active tab left or right
- You can also drag tabs in the tab bar to reorder them manually
- `Ctrl+1` through `Ctrl+9` jump directly to tab 1 through 9 in this repo's kitty config

## Moving A Window Back Into Another OS Window As A Tab

- Kitty calls this action `detach_window`
- In this repo's kitty config, `Ctrl+F2` moves the current window into the previously active tab
- In this repo's kitty config, `Ctrl+F3` moves the current window into a new tab
- In this repo's kitty config, `Ctrl+F4` prompts for a target tab or window
- Recent kitty versions also let you drag a tab in the tab bar between OS windows
