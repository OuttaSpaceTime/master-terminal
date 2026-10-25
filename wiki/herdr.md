---
title: Herdr
tags: [herdr, terminal, agents, theme, colors, chezmoi, keybindings, mouse]
created: 2026-09-22
updated: 2026-10-25
---

# Herdr

Terminal workspace manager for AI coding agents (panes, workspaces, a background
server that keeps agents alive across disconnects). Single Rust binary.

## Current setup

- Install: `curl -fsSL https://herdr.dev/install.sh | sh`. Goes to `~/.local/bin/herdr` (on PATH),
  verifies a SHA-256 from `herdr.dev/latest.json`, needs no sudo, edits no shell rc.
  Update with `herdr update`; channel is `stable` by default (`herdr channel set preview`).
- Config: `home/private_dot_config/herdr/config.toml` → `~/.config/herdr/config.toml`.
- Theme: `theme.name = "catppuccin-latte"` plus `[theme.custom]` overrides with the exact hexes
  from [Light Theme Palette](light-theme-palette.md).
- Plugins (links live in `~/.config/herdr/plugins.json`, outside chezmoi; redo once per machine):
  - `herdr plugin link ~/.local/share/nvim/lazy/smart-splits.nvim` (`ctrl+h/j/k/l`)
  - `herdr plugin link ~/.config/herdr/smart-resize` (`alt+h/j/k/l`; source
    `home/private_dot_config/herdr/smart-resize/`, tested by `tests/test_herdr_smart_resize.py`)
- `ui.window_title = "herdr: {workspace}"` lets kitty recognise the herdr window (see the nvim gotcha).

### Kitty keys inside herdr

Inside herdr, kitty's split and tab keys drive herdr instead (prefix bindings still work). A kitty
tab maps to a herdr workspace (both are sidebar rows), a kitty split to a herdr pane.

| Key | herdr action |
|---|---|
| `ctrl+h/j/k/l` | `smart-splits.nvim.*` (see the nvim gotcha) |
| `ctrl+shift+d` / `ctrl+shift+enter` / `ctrl+shift+s` | `split_vertical` / `split_vertical` / `split_horizontal` |
| `ctrl+shift+w` | `close_pane` |
| `ctrl+shift+[` / `]` | `cycle_pane_previous` / `next` |
| `ctrl+alt+shift+h/j/k/l` | `swap_pane_*` |
| `alt+shift+h` / `alt+shift+l` | `previous_agent` / `next_agent` |
| `alt+h/j/k/l` | `smart-resize.*`: resizes the nvim split when nvim is focused, else the herdr pane |
| `f6` / `ctrl+shift+r` | `zoom` / `resize_mode` |
| `ctrl+shift+h` / `ctrl+shift+l` | `previous_tab` / `next_tab` (herdr tabs) |
| `ctrl+shift+n` | `new_tab` (asks for a name; Enter keeps the number) |
| `ctrl+shift+m` | `rename_tab` |
| `ctrl+1..9` | `switch_workspace` |
| `ctrl+alt+h` / `ctrl+alt+l` | `previous_workspace` / `next_workspace` |
| `ctrl+shift+t` / `ctrl+shift+q` / `ctrl+alt+shift+t` | `new_workspace` / `close_workspace` / `rename_workspace` |
| `ctrl+shift+g` / `ctrl+shift+o` / `ctrl+shift+x` | `new_worktree` / `open_worktree` / `remove_worktree` |

- `ctrl+shift+left/right` and `ctrl+tab` stay with kitty, so they still switch kitty tabs from a herdr window.
- A worktree is an ordinary herdr workspace. Menu "Close" is `close_workspace` and keeps checkout and
  branch. "Delete worktree checkout..." (`remove_worktree`) runs `git worktree remove` and keeps the
  branch (`src/client/shell/context_menu.rs`).
- `ctrl+alt+?` is a kitty map, not a herdr key. It opens `home/private_dot_config/kitty/herdr-keys.txt`
  in `less` as a kitty overlay, in herdr and in plain kitty. Herdr's own help (`ctrl+b ?`) doesn't list
  these keys. kitty matches `ctrl+alt+?` against a real `ctrl+alt+shift+/` through its default
  `allow_fallback shifted`. The sheet is hand-written: update it along with the table.

Every key needs both halves:
- kitty: `map --when-focus-on title:^herdr: <key>` (no action, so the key passes through). It must come
  *after* the map it overrides: of the matching maps, `kitty/keys.py` `matching_key_actions` keeps the
  last one defined.
- herdr: the same chord as a direct binding (`new_workspace = ["prefix+shift+n", "ctrl+shift+t"]`).

`tests/test_kitty_herdr_keys.py` fails if the two sets drift apart. herdr pushes kitty's keyboard flags
(`DISAMBIGUATE_ESCAPE_CODES`, `src/input/model.rs`), so `ctrl+shift+t` and `ctrl+1` reach it intact.

## How to

- Show the active keymap: `prefix+?` (then `/` to filter). Navigate mode is `prefix+w`:
  `up`/`down` switch workspaces, `h/j/k/l` or `left`/`right` switch panes.
- Full defaults for the installed version (`herdr --default-config` omits some, see Gotchas):

  ```bash
  curl -fsSL "https://raw.githubusercontent.com/herdrdev/herdr/v$(herdr --version | cut -d' ' -f2)/docs/next/website/src/data/config-reference.json" \
    | jq -r '.sections[].keys[] | select(.key|startswith("keys.")) | "\(.key)\t\(.default|tostring)"'
  ```
- Validate config: `herdr config check` reads `$HERDR_CONFIG_PATH` (not `$HERDR_CONFIG`); point it at the
  chezmoi source before applying. Reload a running server: `herdr server reload-config`.
- Built-in light themes (`src/config/theme.rs`, `THEME_NAMES`): `catppuccin-latte`, `tokyo-night-day`,
  `gruvbox-light`, `one-light`, `solarized-light`, `kanagawa-lotus`, `rose-pine-dawn`. `terminal` follows
  the host terminal's ANSI palette.
- Overridable `[theme.custom]` tokens (all optional): `accent panel_bg sidebar_bg active_row_bg
  selection_bg surface0 surface1 surface_dim overlay0 overlay1 text subtext0 mauve green yellow red
  blue teal peach`. `surface0/1` and `overlay0/1` stay at latte's defaults (our palette is latte
  derived). Colors accept hex, named colors, `rgb(r,g,b)`, or `reset`/`default`/`none`/`transparent`.
- Verify colors with the render probe, not screenshots: run herdr in a sized PTY and count truecolor SGR
  codes, as in [Light Theme Palette](light-theme-palette.md):

  ```bash
  python3 render_probe.py after.raw 4   # pty.fork + TIOCSWINSZ 40x120, SIGTERM after N s
  grep -oE '48;2;[0-9]+;[0-9]+;[0-9]+' after.raw | sort | uniq -c | sort -rn
  ```

  Mocha leaked as `48;2;24;24;37` (`#181825`) and `38;2;205;214;244` (`#cdd6f4`); the fixed theme has
  zero dark tokens. Script: `.solve/tasks/2026-09-22-herdr-theme/`.
- Verify the kitty keys really act: run `.solve/tasks/2026-10-02-herdr-kitty-keys/probe.py`. It starts an
  isolated herdr (own `XDG_CONFIG_HOME`, worktree dir and cwd inside the sandbox) in a separate minimized
  `kitty --config NONE`, presses each chord with `kitten @ send-key` and compares `herdr api snapshot`.
  Keep `PROBE_DIR` short (`mktemp -d /tmp/claude-1000/hk.XXXX`): Unix socket paths over ~108 chars fail
  silently. For agent steps, a copy of `sleep` named `claude` counts as a Claude agent
  (`herdr agent explain` shows it). About 1 run in 4 kitty sends a few keys in the legacy encoding
  (`^[^L` or a bare `1` instead of `ctrl+alt+l` / `ctrl+1`) and those steps fail; cause unknown (not
  herdr's focus handling), rerun.

## Gotchas

- `theme.name` defaults to `catppuccin` = mocha, dark. With the light kitty background the UI comes out
  half-dark: herdr paints sidebar/panels/status in mocha while the pane area shows `#fafafa`.
- `herdr --default-config` omits some actions: in 0.9.1 `copy_mode` (`prefix+[`) and `swap_pane_*`
  (`prefix+shift+h/j/k/l`), though `herdr config check` accepts them.
- `│` separators use `surface_dim`, which latte sets to `#e6e9ef`: nearly invisible on `#fafafa`/`#f0f0f2`.
  Matches upstream intent (mocha is equally faint); set `surface_dim = "#ccd0da"` for visible borders.
- Herdr writes `onboarding = false` into `config.toml` on first run, and picking a theme in Settings
  writes `theme.name` too (and disables `auto_switch`). It does not rewrite the file wholesale (empty
  `chezmoi -S home diff` after a restart), but Settings changes show up as drift.
- `herdr config check` only validates keys/values, not readability; use the render probe.
- A bare `script -qec herdr /dev/null` fails with `terminal reported a zero-sized grid` (no controlling
  tty, 0x0 winsize). Set `TIOCSWINSZ` explicitly.
- nvim `ctrl+h/j/k/l` dies inside herdr. kitty maps them to `neighboring_window` and passes them through
  only when the focused window has `var:IS_NVIM`, which smart-splits sets via `OSC 1337 SetUserVar`.
  herdr emulates its panes, so that OSC never reaches kitty (`kitten @ ls` showed `user_vars: {}` on the
  herdr window with three nvims inside; a plain kitty tab got `IS_NVIM`). Also, forcing
  `smart_splits_multiplexer_integration = "kitty"` skips smart-splits' herdr auto-detection, and kitty's
  `cmdline:` match sees the window's initial zsh, not the foreground herdr.
  Fix: herdr `ui.window_title = "herdr: {workspace}"` + kitty `map --when-focus-on title:^herdr: ctrl+h`
  (etc.) passes the keys to herdr; smart-splits' herdr plugin (`[[keys.command]]` →
  `smart-splits.nvim.left` etc.) forwards them to nvim or moves herdr focus; no forced kitty backend in
  `smart-splits.lua`. `alt+h/j/k/l` resize works the same way through `smart-resize`.

## Tried and rejected

- Focus on hover: up to 0.9.3 there is no focus-follows-mouse option. Only a left click focuses a pane;
  pointer motion is forwarded to the app inside (`src/client/shell/mouse.rs`, `MouseEventKind::Moved`).
  kitty's `focus_follows_mouse yes` stops at the herdr window. A plugin can't add it: plugin and socket
  APIs emit no mouse events.
- Forks with `ui.focus_follows_mouse` (default off), e.g. `noomz/herdr` branch `feat/focus-follows-mouse`
  (200 ms dwell): building locally needs Zig 0.16 for the vendored libghostty-vt on top of the pinned
  Rust toolchain, and `herdr update` would overwrite the result.

## Upstream

- Focus on hover: Discussion [#1259](https://github.com/herdrdev/herdr/discussions/1259) (upvoted and
  commented 2026-10-06, subscribed; status as of 2026-10-06: tracked, no option yet). Feature requests go
  to Discussions, not Issues; new duplicates get closed.
