---
title: Pop Shell
tags: [gnome, pop-shell, tiling, hotkeys, shortcuts, desktop]
created: 2026-09-11
updated: 2026-10-25
---

# Pop Shell

System76's auto-tiling GNOME extension, installed from source on Ubuntu 24.04. It replaces the
hand-rolled `h/j/k/l` tiling scheme that used to live in `apply-gnome-shortcuts` plus `tiling-assistant`.

## Current setup

No Ubuntu package exists (Fedora, Arch, openSUSE and Gentoo have one; `apt-cache search pop-shell` finds
nothing), so it is built from source. Branch by GNOME version:

Branch by GNOME version: 3.36–41 `master_focal`, 42–44 `master_jammy`, 45 `master_mantic`,
46+ `master_noble`.

This machine: Ubuntu 24.04.4 / GNOME Shell 46 / Wayland, so `master_noble` (also the repo default
branch; its `metadata.json` declares `shell-version` 45–50).

Pop Shell starts in **floating mode** (normal GNOME stacking, plus Pop's focus keys). `Super+Y` toggles
**auto-tiling**. `Super+Enter` enters **adjustment mode** on the focused window, a modal state where plain
`h/j/k/l` move, resize and swap; `Return` accepts, `Escape` reverts.

Keys below come from the installed schema (`schemas/org.gnome.shell.extensions.pop-shell.gschema.xml`),
not the docs.

### Always active
- Super H / J / K / L: move focus left / down / up / right
- Super Shift H / L: move window to monitor left / right; Super Shift J / K: to workspace down / up
- Super Ctrl Shift J / K: move window to monitor down / up
- Super Enter: adjustment mode; Super Y: toggle auto-tiling; Super G: toggle floating for the window
- Super O: toggle tiling orientation (horizontal/vertical split); Super S: toggle stacking mode
- Super /: launcher (**does not work here**, see Gotchas)

Arrow keys and keypad work everywhere `h/j/k/l` do.

### Adjustment mode (after Super+Enter)
- `H/J/K/L`: move window within the tree
- `Shift H/J/K/L`: resize
- `Ctrl H/J/K/L`: swap with the window in that direction
- `O`: toggle orientation of this fork
- `Return`: accept; `Escape`: cancel and revert

### GNOME keys that `configure.sh` rewrote
- Super Q: close window (was Super Shift Q)
- Super M: toggle maximized; Super comma: minimize; Super V: toggle message tray
- Super Escape: lock screen (was Super B; now Alt Escape, see [GNOME](gnome.md))
- Super T: terminal (launches kitty); Super B: web browser; Super E: email; Super F: home folder
- Ctrl Super J / K: switch workspace down / up

It also **cleared** `maximize`, `unmaximize`, `toggle-tiled-left/right`, `move-to-monitor-*`,
`switch-to-workspace-left/right` and `toggle-overview`, and enabled `native-window-placement` plus
`workspaces-only-on-primary false`.

### Settings deviating from upstream defaults

Pop Shell's schema is not in the default schema dir, so `gsettings` needs `--schemadir`:

```bash
S=~/.local/share/gnome-shell/extensions/pop-shell@system76.com/schemas
gsettings --schemadir "$S" get org.gnome.shell.extensions.pop-shell active-hint
```

GUI: `gnome-extensions prefs pop-shell@system76.com`.

| Setting | Default | Here | Why |
|---|---|---|---|
| `active-hint` | `false` | `true` | See where keyboard focus landed |
| `mouse-cursor-focus-location` | `0` | `4` | Pointer lands centred, not in the corner |
| `gap-inner` / `gap-outer` | `2` / `2` | `4` / `4` | 2px is too tight to read |
| `smart-gaps` | `false` | `true` | Drop the outer gap for a lone window |

`mouse-cursor-focus-location` indexes `FocusPosition` in `focus.js`:
`0=TopLeft 1=TopRight 2=BottomLeft 3=BottomRight 4=Center`. `hint-color-rgba` stays at upstream orange
`rgba(251, 184, 108, 1)`, which clashes with the [light theme palette](light-theme-palette.md).

`mouse-cursor-follows-active-window` defaults to `true`: the pointer warps to the window focused by
keyboard shortcut or touchpad gesture, never on mouse-driven focus changes. This supersedes the local
`mousefollowsfocus-local@felix.local` fork; fork and upstream both stay disabled, see
[Mouse Follows Focus](mouse-follows-focus.md).

## How to

Install:

```bash
dconf dump /org/gnome/ > ~/gnome-dconf-backup-$(date +%Y%m%d).conf
gnome-extensions disable tiling-assistant@ubuntu.com
git clone --depth 1 -b master_noble https://github.com/pop-os/shell ~/src/pop-shell
cd ~/src/pop-shell && echo y | make local-install
```

Build deps are `make` + `tsc` (>= 3.8) + `node`. `make local-install` runs `scripts/configure.sh`, which
prompts `Pop shell will override your default shortcuts. Are you sure? (y/n)`; piping `y` answers it. It
writes a `.confirm_shortcut_change` marker in the repo, and a second run then *skips* the keybinding
writes. On Wayland, add the UUID to `org.gnome.shell enabled-extensions` directly (see Gotchas); it loads
on next login.

Verify the `apply-gnome-shortcuts` conflict stays resolved: snapshot the contested dconf paths, run the
script, diff. The snapshots must be identical.

Revert:

```bash
cd ~/src/pop-shell && make uninstall
dconf load /org/gnome/ < ~/gnome-dconf-backup-YYYYMMDD.conf
```

The deleted lines of `apply-gnome-shortcuts` are recoverable from git history.

## Gotchas

- **`apply-gnome-shortcuts` fought Pop Shell.** `~/.local/bin/apply-gnome-shortcuts --login` runs from a
  GNOME autostart entry and reapplies its bindings at 0s, +5s, +20s and +50s ("login races do not win"),
  so it would have undone `configure.sh` about a minute after every login. Resolution: the colliding block
  was deleted from `home/dot_local/bin/executable_apply-gnome-shortcuts`; Pop Shell owns all window,
  monitor, workspace and tiling movement. The script kept only what Pop Shell does not touch:
  `dynamic-workspaces false`, `num-workspaces 4`, clearing `switch-to-application-1..9` (Super+1–4 switch
  workspaces, see [GNOME](gnome.md)), kitty as `default-applications.terminal`, and the Super+Shift+I
  headset toggle (`custom0`).
- **`gnome-extensions enable` fails on Wayland** (last `make` target) with
  `Extension "pop-shell@system76.com" does not exist`: GNOME Shell has not rescanned the extension
  directory and cannot be restarted in place. `make restart-shell` is a deliberate no-op when
  `WAYLAND_DISPLAY` is set. Log out and back in.
- **Enable state is two dconf keys.** `org.gnome.shell enabled-extensions` and `disabled-extensions` are
  separate lists, and the running shell can diverge from both: the mouse-follows-focus fork showed up in
  `gnome-extensions list --enabled` while sitting in `disabled-extensions`, and silently stopped loading
  after logout. `gnome-extensions info <uuid>` queries the **live shell**, not the filesystem (right after
  install on Wayland it reports `doesn't exist`). To make an enable survive logout, confirm the UUID
  moved out of `disabled-extensions`, not just that the runtime reports `ACTIVE`.
- **The launcher does not work.** `launcher.js:278` spawns `['pop-launcher']`, a separate Rust binary not
  packaged for Ubuntu and not installed; `Super+/` fails silently. Build it from `pop-os/launcher` if
  ever wanted.
- `tiling-assistant@ubuntu.com` must stay disabled; two auto-tilers fight.
- Pop's own GNOME Shell theme is not present, so tiling hints use the stock GNOME look.
- Do **not** revert via the README's "Reset All" in GNOME Keyboard Settings: it also wipes custom
  keybindings. Use the dconf dump.

## Tried and rejected

- Local `mousefollowsfocus-local@felix.local` fork: hooked the generic window `focus` signal, could not
  tell keyboard from mouse origin, needed a 2000ms suppression window plus an unresolved kitty title-bar
  bug to compensate. Pop Shell's own option replaces it.
