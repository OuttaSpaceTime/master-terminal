---
title: Pop Shell
tags: [gnome, pop-shell, tiling, hotkeys, shortcuts, desktop]
created: 2026-09-11
updated: 2026-09-11
---

# Pop Shell

System76's auto-tiling GNOME extension, installed from source on Ubuntu 24.04.
It replaces the hand-rolled `h/j/k/l` tiling scheme that used to live in
`apply-gnome-shortcuts` plus `tiling-assistant`.

## Why it works on Ubuntu

There is no Ubuntu package (Fedora, Arch, openSUSE and Gentoo have one; `apt-cache
search pop-shell` finds nothing), so it is built from source. Branch selection is by
GNOME version:

| GNOME | Branch |
|---|---|
| 3.36–41 | `master_focal` |
| 42–44 | `master_jammy` |
| 45 | `master_mantic` |
| 46+ | `master_noble` |

This machine is Ubuntu 24.04.4 / GNOME Shell 46 / Wayland, so `master_noble` — which is
also the repo default branch. Its `metadata.json` declares `shell-version` 45–50.

## Install

```bash
dconf dump /org/gnome/ > ~/gnome-dconf-backup-$(date +%Y%m%d).conf
gnome-extensions disable tiling-assistant@ubuntu.com
git clone --depth 1 -b master_noble https://github.com/pop-os/shell ~/src/pop-shell
cd ~/src/pop-shell && echo y | make local-install
```

Build deps are `make` + `tsc` (>= 3.8) + `node`; all were already present.

Notes:

- `make local-install` runs `scripts/configure.sh`, which prompts
  `Pop shell will override your default shortcuts. Are you sure? (y/n)`.
  Piping `y` answers it non-interactively. It writes a `.confirm_shortcut_change`
  marker in the repo, and a second run then *skips* the keybinding writes.
- The final `make` target is `gnome-extensions enable`, which fails with
  `Extension "pop-shell@system76.com" does not exist` on Wayland — GNOME Shell has not
  rescanned the extension directory yet and cannot be restarted in place. Add the UUID
  to `org.gnome.shell enabled-extensions` directly instead; it loads on next login.
- `make restart-shell` is a deliberate no-op when `WAYLAND_DISPLAY` is set. Log out and
  back in to activate.

## Two modes

Pop Shell starts in **floating mode** (normal GNOME stacking, plus Pop's focus keys).
`Super+Y` toggles **auto-tiling**, where every window is placed into a tiling tree.

`Super+Enter` enters **adjustment mode** on the focused window — a modal state where the
plain `h/j/k/l` keys move, resize and swap. `Return` accepts, `Escape` reverts.

## Keybindings

All of these are read from the installed schema
(`schemas/org.gnome.shell.extensions.pop-shell.gschema.xml`), not from the docs.

### Always active

| Shortcut | Action |
|---|---|
| Super H / J / K / L | Move focus left / down / up / right |
| Super Shift H / L | Move window to monitor left / right |
| Super Shift J / K | Move window to workspace down / up |
| Super Ctrl Shift J / K | Move window to monitor down / up |
| Super Enter | Enter adjustment mode |
| Super Y | Toggle auto-tiling on/off |
| Super G | Toggle floating for the focused window |
| Super O | Toggle tiling orientation (horizontal/vertical split) |
| Super S | Toggle stacking mode |
| Super / | Launcher (**does not work here**, see gaps) |

Arrow keys and keypad work everywhere `h/j/k/l` do.

### Adjustment mode (after Super+Enter)

| Shortcut | Action |
|---|---|
| H / J / K / L | Move window within the tree |
| Shift H / J / K / L | Resize |
| Ctrl H / J / K / L | Swap with the window in that direction |
| O | Toggle orientation of this fork |
| Return | Accept |
| Escape | Cancel and revert |

### GNOME keys that `configure.sh` rewrote

| Shortcut | Action |
|---|---|
| Super Q | Close window (was Super Shift Q) |
| Super M | Toggle maximized |
| Super comma | Minimize |
| Super V | Toggle message tray |
| Super Escape | Lock screen (was Super B) |
| Super T | Terminal (launches kitty) |
| Super B | Web browser |
| Super E | Email |
| Super F | Home folder |
| Ctrl Super J / K | Switch workspace down / up |

It also **cleared** `maximize`, `unmaximize`, `toggle-tiled-left/right`,
`move-to-monitor-*`, `switch-to-workspace-left/right` and `toggle-overview`, and enabled
`native-window-placement` plus `workspaces-only-on-primary false`.

## Conflict with apply-gnome-shortcuts

This was the load-bearing problem. `~/.local/bin/apply-gnome-shortcuts --login` runs from
a GNOME autostart entry and reapplies its bindings at 0s, +5s, +20s and +50s — explicitly
so "login races do not win". That is engineered to beat Pop Shell, and it would have
silently undone `configure.sh` roughly a minute after every login.

Resolution: the colliding block was deleted from
`home/dot_local/bin/executable_apply-gnome-shortcuts`. Pop Shell now owns all window,
monitor, workspace and tiling movement. The script kept only what Pop Shell does not touch:

- `dynamic-workspaces false`, `num-workspaces 4`
- clearing `switch-to-application-1..9` so dash-to-panel owns Super+1–9
- kitty as `default-applications.terminal`
- the Super+Shift+I headset toggle (`custom0`)

Verify the conflict stays resolved by snapshotting the contested dconf paths, running the
script, and diffing — the two snapshots must be identical.

## Settings

Pop Shell's schema is not in the default schema dir, so `gsettings` needs `--schemadir`:

```bash
S=~/.local/share/gnome-shell/extensions/pop-shell@system76.com/schemas
gsettings --schemadir "$S" get org.gnome.shell.extensions.pop-shell active-hint
```

There is also a GUI: `gnome-extensions prefs pop-shell@system76.com`.

Values set here, deviating from upstream defaults:

| Setting | Default | Here | Why |
|---|---|---|---|
| `active-hint` | `false` | `true` | See where keyboard focus landed |
| `mouse-cursor-focus-location` | `0` | `4` | Pointer lands centred, not in the corner |
| `gap-inner` / `gap-outer` | `2` / `2` | `4` / `4` | 2px is too tight to read |
| `smart-gaps` | `false` | `true` | Drop the outer gap for a lone window |

`mouse-cursor-focus-location` is an index into `FocusPosition` in `focus.js`:
`0=TopLeft 1=TopRight 2=BottomLeft 3=BottomRight 4=Center`.

`hint-color-rgba` is left at upstream orange `rgba(251, 184, 108, 1)`, which clashes with
the [light theme palette](light-theme-palette.md).

## Mouse follows focus

`mouse-cursor-follows-active-window` defaults to `true`: the pointer warps to the window
you focus with a keyboard shortcut or touchpad gesture. Because it triggers only on
keyboard and gesture input, it never warps on mouse-driven focus changes.

This supersedes the local `mousefollowsfocus-local@felix.local` fork, which hooked the
generic window `focus` signal, could not tell keyboard from mouse origin, and needed a
2000ms suppression window plus an unresolved kitty title-bar bug to compensate. The fork
and its upstream both stay disabled — see [Mouse Follows Focus](mouse-follows-focus.md).

## Extension enable state is two dconf keys

`org.gnome.shell enabled-extensions` and `disabled-extensions` are separate lists, and the
*running* shell's state can diverge from both. During this install the fork showed up in
`gnome-extensions list --enabled` while sitting in `disabled-extensions`; it silently
stopped loading after logout. Two consequences:

- `gnome-extensions info <uuid>` queries the **live shell**, not the filesystem. Right
  after installing on Wayland it reports `doesn't exist` even though the files are there.
- To make an enable survive logout, confirm the UUID actually moved out of
  `disabled-extensions`, not just that the runtime reports `ACTIVE`.

## Known gaps on Ubuntu

- **The launcher does not work.** `launcher.js:278` spawns `['pop-launcher']`, a separate
  Rust binary that is not packaged for Ubuntu and is not installed. `Super+/` fails
  silently. Build it from `pop-os/launcher` if it is ever wanted.
- `tiling-assistant@ubuntu.com` must stay disabled; two auto-tilers fight.
- Pop's own GNOME Shell theme is not present, so tiling hints use the stock GNOME look.

## Reverting

```bash
cd ~/src/pop-shell && make uninstall
```

Then restore the shortcut half. Do **not** use the README's advice to hit "Reset All" in
GNOME Keyboard Settings — that also wipes the custom keybindings. Use the dconf dump taken
before install:

```bash
dconf load /org/gnome/ < ~/gnome-dconf-backup-YYYYMMDD.conf
```

The deleted lines of `apply-gnome-shortcuts` are recoverable from git history.
