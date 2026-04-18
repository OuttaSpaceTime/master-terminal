---
title: Mouse Follows Focus
tags: [gnome, extension, mouse, focus]
created: 2026-04-14
updated: 2026-04-14
---

# Mouse Follows Focus

Upstream installed extension path:

- `~/.local/share/gnome-shell/extensions/mousefollowsfocus@matthes.biz/`

Local fork managed in this repo:

- source: `home/dot_local/share/gnome-shell/extensions/mousefollowsfocus-local@felix.local/`
- deployed: `~/.local/share/gnome-shell/extensions/mousefollowsfocus-local@felix.local/`
- UUID: `mousefollowsfocus-local@felix.local`

Recommended chezmoi management model:

- Manage the deployed extension payload under `home/dot_local/share/gnome-shell/extensions/<uuid>/`
- That maps to `~/.local/share/gnome-shell/extensions/<uuid>/`
- Treat the upstream GitHub repo as an import source, not as the runtime location
- If desired, keep a separate clone elsewhere for upstream sync, but the installed extension should still be rendered from chezmoi source

Root cause of the "mouse switch should not warp pointer" behavior:

- `extension.js` connects every normal window's `focus` signal to `focus_changed()`
- `focus_changed()` warps the pointer for any focus change where the pointer is not already inside the focused window
- There is no check for whether the focus change came from a keyboard shortcut or a mouse action
- Because of that, clicking a dock icon, panel item, or other mouse-driven app switch still triggers pointer warping

Validated findings from implementing the fork:

- GNOME Shell accepts a forked copy of the extension as long as it has its own UUID and lives under `~/.local/share/gnome-shell/extensions/<uuid>/`
- The UUID needs to be email-style. `mousefollowsfocus-local@felix.local` worked; `mousefollowsfocus-local@felix` did not
- `gnome-extensions disable/enable` does not reload JS bytecode
- Logout/login alone does not reload JS bytecode either — GJS caches compiled extension code across sessions
- `gnome-extensions install --force` (from a zip) also does not bust the bytecode cache
- The only confirmed way to force fresh code loading: disable → remove the extension directory entirely → logout/login → restore directory → enable
- `console.log()`, `console.error()`, `global.log()`, and `GLib.file_set_contents()` from extensions all produce no visible output on Ubuntu Wayland GNOME 46 — Ubuntu redirects gnome-shell stdout/stderr away from journalctl
- Extension developers on Wayland typically use `dbus-run-session gnome-shell --nested --wayland` for iteration, which runs a fresh shell in a window with live console output

Working reload workflow:

1. Edit `home/dot_local/share/gnome-shell/extensions/mousefollowsfocus-local@felix.local/extension.js`
2. Deploy with `chezmoi -S home apply --force ~/.local/share/gnome-shell/extensions/mousefollowsfocus-local@felix.local`
3. Disable: `gnome-extensions disable mousefollowsfocus-local@felix.local`
4. Remove deployed dir: `rm -rf ~/.local/share/gnome-shell/extensions/mousefollowsfocus-local@felix.local`
5. Log out and back in
6. Restore: `chezmoi -S home apply --force ~/.local/share/gnome-shell/extensions/mousefollowsfocus-local@felix.local/`
7. Enable: `gnome-extensions enable mousefollowsfocus-local@felix.local`
8. Verify with:
   - `gnome-extensions info mousefollowsfocus-local@felix.local`
   - `gnome-extensions info mousefollowsfocus@matthes.biz`

Expected post-login state:

- fork: `Enabled: Yes`, `State: ACTIVE`
- upstream: `Enabled: No`, `State: INACTIVE`

Current fork behavior on disk:

- The fork keeps the upstream focus-warp logic
- It adds a short pointer-driven suppression window for mouse/touch activation
- `KEY_PRESS` clears that suppression so the next keyboard-driven switch can still warp normally
- `BUTTON_PRESS`, `BUTTON_RELEASE`, `TOUCH_BEGIN`, and `TOUCH_END` extend suppression
- The current suppression window is `2000ms`

Why this implementation:

- Positive keyboard-origin detection turned out to be fragile because GNOME Shell may consume global shortcuts before extension hooks see them reliably
- Negative gating is simpler: keep the upstream warp behavior, but suppress it immediately after pointer-driven activation
- Clearing suppression on keyboard press avoids blocking a quick keyboard switch that follows a mouse interaction

Known bug — kitty title bar mouse warp:

- Moving the mouse cursor down from the top bar to kitty's title bar causes the cursor to jump to center
- Does not happen with other windows (GTK/CSD apps)
- Likely caused by the extension's `cursor_within_window` check failing for SSD windows, or by sloppy-focus triggering a focus change from mouse motion (which the suppression logic doesn't cover — it only tracks button/touch events, not motion)
- Potential fix directions: (1) add short motion-event suppression (~150ms) so mouse-driven focus changes don't warp, (2) use union of frame_rect and buffer_rect for the cursor containment check to handle SSD windows
- Not yet verified due to the bytecode caching and logging difficulties described above

Troubleshooting notes:

- If `gnome-extensions info` shows stale metadata or behavior after a code change, assume the running shell still has stale JS loaded
- GJS bytecode caching means the running shell is almost certainly using stale code unless the full remove+restore reload workflow was followed
- The Extensions UI showing a toggle as enabled is not enough to prove new code is running
- For iterative development, use a nested shell: `dbus-run-session gnome-shell --nested --wayland`

Why this belongs in the extension:

- The bug is caused by the extension reacting to a generic window-focus signal without preserving input origin
- GNOME shortcut config in this repo cannot distinguish hotkey-triggered focus changes from mouse-triggered ones after the fact

Alternatives to the extension system:

- On GNOME Wayland, focus events and window geometry are locked inside the compositor — no external process can access them directly
- A standalone daemon would still need helper extensions to expose focus changes and window rects via D-Bus (e.g. "Focused Window D-Bus" + "Window Commander" extensions), plus ydotool for cursor warping
- This trades one extension for two simpler ones plus a daemon — easier to iterate on (normal logging, just restart service) but adds complexity and ydotool latency (~50-200ms)
- Not worth pursuing unless the extension development experience becomes untenable

Recommended development workflow (if revisiting):

- Use `dbus-run-session gnome-shell --nested --wayland` for iterative development
- The nested shell runs in a window with live console output in the launching terminal
- Extensions reload fresh on each nested shell launch — no cache issues
- Downside: testing precise mouse interactions between top bar and window title bars is awkward in a nested window
- Once the fix is validated in the nested shell, deploy to the real session using the full cache-busting reload workflow above

Upstream context:

- Upstream repo: `https://github.com/LeonMatthes/mousefollowsfocus`
- There is already an open issue about temporarily disabling the behavior during workspace switching, which points to the same missing-context problem around focus changes
