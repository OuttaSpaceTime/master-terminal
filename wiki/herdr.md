---
title: Herdr
tags: [herdr, terminal, agents, theme, colors, chezmoi, keybindings]
created: 2026-09-22
updated: 2026-09-30
---

# Herdr

Terminal workspace manager for AI coding agents (panes, workspaces, a background
server that keeps agents alive across disconnects). Single Rust binary.

## Install

```bash
curl -fsSL https://herdr.dev/install.sh | sh
```

Installs to `~/.local/bin/herdr` (already on PATH), verifies a SHA-256 from
`herdr.dev/latest.json`, needs no sudo and edits no shell rc. Update with
`herdr update`; channel is `stable` by default (`herdr channel set preview`).

## Keybindings

`prefix+?` (then `/` to filter) shows the active keymap. `herdr --default-config`
leaves some actions out: in 0.9.1 it omits `copy_mode` (`prefix+[`) and
`swap_pane_*` (`prefix+shift+h/j/k/l`), even though `herdr config check` accepts
them. The full list of defaults for the installed version:

```bash
curl -fsSL "https://raw.githubusercontent.com/herdrdev/herdr/v$(herdr --version | cut -d' ' -f2)/docs/next/website/src/data/config-reference.json" \
  | jq -r '.sections[].keys[] | select(.key|startswith("keys.")) | "\(.key)\t\(.default|tostring)"'
```

Navigate mode is `prefix+w` ("workspace navigation"): `up`/`down` switch workspaces,
`h/j/k/l` or `left`/`right` switch panes. The only custom bindings are direct
`ctrl+h/j/k/l` → `smart-splits.nvim.*` (see the nvim gotcha below).

## Theme

`theme.name` defaults to **`catppuccin`**, which is catppuccin *mocha* — dark.
With our light kitty background the UI comes out half-dark: herdr paints its own
sidebar/panels/status in mocha while the pane area shows through as `#fafafa`.
Fix is `theme.name = "catppuccin-latte"` plus `[theme.custom]` overrides pulling
the exact hexes from [Light Theme Palette](light-theme-palette.md).

Source: `home/private_dot_config/herdr/config.toml` → `~/.config/herdr/config.toml`.

Built-in light themes (from `src/config/theme.rs`, `THEME_NAMES`):
`catppuccin-latte`, `tokyo-night-day`, `gruvbox-light`, `one-light`,
`solarized-light`, `kanagawa-lotus`, `rose-pine-dawn`. Also `terminal`, which
makes herdr follow the host terminal's ANSI palette instead of a built-in.

Overridable tokens (all optional, layered on top of the base theme):
`accent panel_bg sidebar_bg active_row_bg selection_bg surface0 surface1
surface_dim overlay0 overlay1 text subtext0 mauve green yellow red blue teal
peach`. `surface0/1`, `overlay0/1` are left at latte's defaults — our palette is
catppuccin-latte derived, so they already match.

Colors accept hex, named colors, `rgb(r,g,b)`, or `reset`/`default`/`none`/
`transparent`. `herdr config check` validates the file; `herdr server reload-config`
reloads a running server.

### Ground-truth probe instead of screenshots

Herdr is a TUI, so verify colors by running it in a sized PTY and counting the
truecolor SGR codes it emits — same idea as the kitty/nvim probes in
[Light Theme Palette](light-theme-palette.md):

```bash
python3 render_probe.py after.raw 4   # pty.fork + TIOCSWINSZ 40x120, SIGTERM after N s
grep -oE '48;2;[0-9]+;[0-9]+;[0-9]+' after.raw | sort | uniq -c | sort -rn
```

Before the fix: `48;2;24;24;37` (`#181825` mocha mantle) ×43 and
`38;2;205;214;244` (`#cdd6f4` mocha text) ×85. After: zero dark tokens.
Script kept at `.solve/tasks/2026-09-22-herdr-theme/`.

## Gotchas

- A bare `script -qec herdr /dev/null` fails with `terminal reported a zero-sized
  grid` — no controlling tty means a 0x0 winsize. Set `TIOCSWINSZ` explicitly.
- `│` separators are painted with `surface_dim`, which latte sets to `#e6e9ef` —
  nearly invisible on our `#fafafa`/`#f0f0f2` surfaces. That matches upstream
  intent (mocha's `#1e1e2e` on `#181825` is equally faint); set
  `surface_dim = "#ccd0da"` if visible panel borders are wanted.
- Herdr writes `onboarding = false` into `config.toml` itself on first run, and
  picking a theme in Settings writes `theme.name` too (and disables
  `auto_switch`). A `chezmoi -S home diff` after a server restart came back
  empty, so it does not rewrite the file wholesale — but Settings changes will
  show up as drift, like `~/.claude/settings.json` used to.
- `herdr config check` only validates keys/values. It does not tell you whether
  the result is readable; that needs the render probe.
- nvim `ctrl+h/j/k/l` dies inside herdr. kitty maps those keys to
  `neighboring_window` and only passes them through when the focused window has
  `var:IS_NVIM`, which smart-splits sets with `OSC 1337 SetUserVar`. herdr
  emulates its panes, so that OSC never reaches kitty: `kitten @ ls` showed
  `user_vars: {}` on the herdr window with three nvims inside, while a plain kitty
  tab printing the same bytes got `IS_NVIM`. On top of that, forcing
  `smart_splits_multiplexer_integration = "kitty"` skips smart-splits' herdr
  auto-detection. kitty's `cmdline:` match sees the window's initial zsh, not the
  foreground herdr, so it can't target the herdr window.
  Fix: herdr `ui.window_title = "herdr: {workspace}"` + kitty
  `map --when-focus-on title:^herdr: ctrl+h` (etc.) passes the keys to herdr;
  smart-splits' herdr plugin (`[[keys.command]]` → `smart-splits.nvim.left` etc.)
  forwards them to nvim or moves herdr focus; no forced kitty backend in
  `smart-splits.lua`. The plugin link lives in `~/.config/herdr/plugins.json`,
  outside chezmoi: redo `herdr plugin link ~/.local/share/nvim/lazy/smart-splits.nvim`
  on a new machine.
