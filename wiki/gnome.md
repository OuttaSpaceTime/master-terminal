---
title: GNOME
tags: [gnome, hotkeys, shortcuts, desktop]
created: 2026-04-10
updated: 2026-10-05
---

# GNOME

Custom hotkeys for the GNOME desktop environment.

> Window movement, tiling, monitor and workspace-direction keys are owned by
> **[Pop Shell](pop-shell.md)** since 2026-09-11. This page covers only what Pop Shell
> does not bind. The old `Super+h/j/k/l` split/maximize scheme documented here is gone.

## Workspace Navigation

| Shortcut | Action |
|---|---|
| Super 1–4 | Switch to workspace 1–4 |
| Shift Super 1–4 | Move window to workspace 1–4 |
| Ctrl Super J / K | Switch workspace down / up (set by Pop Shell) |

Workspaces are static, not dynamic: `dynamic-workspaces false` with `num-workspaces 4`,
applied by `apply-gnome-shortcuts`. The script also pins the Super 1–4 keys above and
clears the old `Shift Alt h / l` `move-to-workspace-left/right` (Super Shift H / L is Pop
Shell's move-to-monitor).

## Window Switching

| Shortcut | Action |
|---|---|
| Alt Tab | Switch windows |
| Super Tab | Switch applications |
| Super ` / Alt ` | Switch windows of an application |
| Alt Escape | Switch windows directly |
| Alt F2 | Run dialog |

## Mouse

| Shortcut | Action |
|---|---|
| Super + Left Click | Move window |
| Super + Right Click | Resize window |

## Dock & Panels

Super 1–9 no longer switches apps. `apply-gnome-shortcuts` clears GNOME Shell's
`switch-to-application-1..9` and sets dash-to-panel's `hot-keys false`. That schema only
ships inside the extension, so it needs
`gsettings --schemadir ~/.local/share/gnome-shell/extensions/dash-to-panel@jderose9.github.com/schemas`.

## System

| Shortcut | Action |
|---|---|
| Super V | Show notifications |
| Super S | Quick settings — **collides with Pop Shell**, see below |
| Super Escape | Lock screen |
| Super Shift I | Toggle WH-1000XM5 headset profile |
| Right Super | Overview |

`toggle-overview` (was `Super+S`) is cleared by Pop Shell's `configure.sh`; the overview
is reachable via the Right Super overlay key.

## Known collisions

- **Super S** is GNOME's `toggle-quick-settings` and Pop Shell's `toggle-stacking-global`.
  Rebind one of them if stacking or quick settings misbehaves.
- **Super Q** is now close-window (Pop Shell). It previously showed the dock.

## Persistence

- GNOME shortcut changes drift back to defaults after login or updates if they are only
  changed in the GUI.
- `~/.local/bin/apply-gnome-shortcuts` runs from a GNOME autostart entry in `--login`
  mode, reapplying at 0s, +5s, +20s and +50s so later session-startup resets do not win.
- That retry loop is aggressive enough to beat other extensions, which is why every
  binding Pop Shell owns was **removed** from the script — otherwise it silently undid
  Pop Shell about a minute after each login. See [Pop Shell](pop-shell.md).
- What the script still pins: static workspaces, Super 1–4 workspace keys, cleared
  `switch-to-application-1..9`, dash-to-panel `hot-keys false`, kitty as default terminal,
  and the Super+Shift+I headset toggle.
