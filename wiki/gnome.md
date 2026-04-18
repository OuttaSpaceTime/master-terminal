---
title: GNOME
tags: [gnome, hotkeys, shortcuts, desktop]
created: 2026-04-10
updated: 2026-04-10
---

# GNOME

Custom hotkeys for the GNOME desktop environment.

## Workspace Navigation

| Shortcut | Action |
|---|---|
| Alt 1–4 | Switch workspaces |
| Super Shift 1–4 | Move to workspace 1–4 |
| Super Alt H / L | Switch to workspace left / right |
| Ctrl Super H / L | Move window to monitor left / right |

## Window Management

| Shortcut | Action |
|---|---|
| Alt Tab / Super Tab | Switch windows |
| Alt Escape | Switch windows directly |
| Super ` | Switch windows of an application |
| Super Shift ` | Switch windows of an app (reverse) |
| Shift Alt ` | Switch windows of an app directly |
| Super H | View split on left |
| Super L | View split on right |
| Super J | Restore window |
| Super K | Maximize window |
| Super Shift Q | Close window |

## Mouse

| Shortcut | Action |
|---|---|
| Super + Left Click | Move window |
| Super + Right Click | Resize window |

## Dock & Panels

| Shortcut | Action |
|---|---|
| Super Q | Show dock |
| Super 1–9 | Toggle apps in dock |

## System

| Shortcut | Action |
|---|---|
| Super V | Show notifications |
| Super S | Quick settings |
| Super Shift L | Lock screen |
| Right Super | Overview |

## Persistence

- GNOME shortcut changes can drift back to defaults after login or updates if they are only changed in the GUI.
- This repo re-applies the custom movement bindings from `~/.local/bin/apply-gnome-shortcuts` via a GNOME autostart entry.
- Current mapping uses `Ctrl+Super+h/l` for monitor movement, `Super+Alt+h/l` for workspace switching, and `Alt+Shift+h/l` for moving windows to the left/right workspace.
- Screen lock is pinned to `Super+Shift+l` through the shortcut script so it survives GNOME resets and login races.
- `tiling-assistant` still ships the old `Super+Left/Right/Up/Down` defaults, but once its own bindings are cleared it no longer suppresses native GNOME defaults for us.
- The durable fix is to run the shortcut script in login mode, which reapplies the `h/j/k/l` mapping immediately and again after delayed retries so later session startup resets do not win.
- Dash-to-panel hotkeys own `Super+1-9` for app launch/switch, so GNOME Shell app-switch bindings for `Super+1-9` are cleared to avoid collisions.
