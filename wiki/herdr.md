---
title: Herdr
tags: [herdr, terminal, agents, theme, colors, chezmoi]
created: 2026-09-22
updated: 2026-09-22
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
