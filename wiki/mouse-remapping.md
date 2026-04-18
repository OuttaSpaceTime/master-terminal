---
title: Mouse Remapping
tags: [mouse, logitech, mx-ergo-s, evdev, trackball, wayland, hidpp, solaar]
created: 2026-04-10
updated: 2026-04-16
---

# Mouse Remapping

## Setup

Tool: `trackball-nav` — a custom Python evdev daemon managed by a systemd user service.
The DPI Switch button is additionally remapped via Solaar HIDpp diversion.

### Chezmoi-managed files

- `home/dot_local/bin/executable_trackball-nav` — the daemon
- `home/private_dot_config/systemd/user/trackball-nav.service` — user service

### System files (not chezmoi — require sudo, reproduce manually)

**`/etc/udev/rules.d/99-mx-ergo-s.rules`**
```
# MX Ergo S: grant input group read/write access to hidraw device
SUBSYSTEM=="hidraw", KERNELS=="0005:046D:B03E.*", MODE="0660", GROUP="input"
# Re-apply HIDpp divert settings on Bluetooth connect
SUBSYSTEM=="hidraw", KERNELS=="0005:046D:B03E.*", ACTION=="add", RUN+="/usr/bin/systemctl --no-block start mx-ergo-s-setup.service"
```

**`/etc/systemd/system/mx-ergo-s-setup.service`**
```ini
[Unit]
Description=Re-apply MX Ergo S HIDpp divert settings on Bluetooth connect
After=bluetooth.service

[Service]
Type=oneshot
User=felix
Environment=LC_ALL=C
ExecStartPre=/bin/sleep 2
ExecStart=/usr/bin/solaar config "MX Ergo S" dpi 500
ExecStart=/usr/bin/solaar config "MX Ergo S" divert-keys "DPI Switch" Diverted
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mx-ergo-s-setup
```

### Prerequisites

```bash
sudo usermod -aG input $USER        # evdev + hidraw access (logout/login required)
sudo apt install python3-evdev solaar
```

### Full reproduction steps (new system)

```bash
# 1. Deploy chezmoi-managed files
chezmoi -S home apply

# 2. Install system files
sudo tee /etc/udev/rules.d/99-mx-ergo-s.rules << 'EOF'
SUBSYSTEM=="hidraw", KERNELS=="0005:046D:B03E.*", MODE="0660", GROUP="input"
SUBSYSTEM=="hidraw", KERNELS=="0005:046D:B03E.*", ACTION=="add", RUN+="/usr/bin/systemctl --no-block start mx-ergo-s-setup.service"
EOF

sudo tee /etc/systemd/system/mx-ergo-s-setup.service << 'EOF'
[Unit]
Description=Re-apply MX Ergo S HIDpp divert settings on Bluetooth connect
After=bluetooth.service

[Service]
Type=oneshot
User=felix
Environment=LC_ALL=C
ExecStartPre=/bin/sleep 2
ExecStart=/usr/bin/solaar config "MX Ergo S" dpi 500
ExecStart=/usr/bin/solaar config "MX Ergo S" divert-keys "DPI Switch" Diverted
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mx-ergo-s-setup
EOF

sudo systemctl daemon-reload
sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=hidraw

# 3. Start user service
systemctl --user enable --now trackball-nav.service

# 4. Apply diversion once manually (first connect before udev rule has fired)
solaar config "MX Ergo S" divert-keys "DPI Switch" Diverted
solaar config "MX Ergo S" dpi 500
```

### Service management

```bash
systemctl --user restart trackball-nav.service   # reload after editing script
systemctl --user status trackball-nav.service     # check if running
journalctl --user -u trackball-nav.service -f     # live logs
journalctl -t mx-ergo-s-setup -n 20              # HIDpp setup service logs
```

After editing the daemon source under `home/`, deploy and restart:

```bash
chezmoi -S home apply ~/.local/bin/trackball-nav
systemctl --user restart trackball-nav.service
```

## Gesture mapping

| Gesture | Action |
|---|---|
| BTN_SIDE tap | Browser back |
| BTN_SIDE + ball left/right | Workspace switch (Super+Alt+H / Super+Alt+L) |
| BTN_SIDE + ball up/down | Move window to workspace (Shift+Alt+H / Shift+Alt+L) |
| BTN_EXTRA tap | Browser forward |
| BTN_EXTRA + ball up/down | App switch (Alt+Tab / Alt+Shift+Tab) |
| BTN_EXTRA + ball left/right | Tab switch (Ctrl+Shift+Tab / Ctrl+Tab) |
| BTN_MIDDLE tap | Middle click |
| BTN_MIDDLE + ball | Scroll (vertical + horizontal) |
| Wheel tilt left (single) | Toggle maximize/unmaximize (Super+K / Super+J, alternating) |
| Wheel tilt left (double, ≤300ms) | Close window (Super+Shift+Q) |
| Wheel tilt right | Copy (Ctrl+C) |
| DPI Switch tap | Enter (via HIDpp diversion — see below) |

Cursor is suppressed during any modifier hold. Tap only fires on release if no ball action occurred.

## DPI Switch → Enter (HIDpp diversion)

The DPI Switch button does not appear in evdev — it speaks Logitech's HIDpp 2.0
protocol over the hidraw interface. The setup has two parts:

**Solaar diversion** (re-applied automatically on each Bluetooth connect by `mx-ergo-s-setup.service`):
- `divert-keys "DPI Switch" Diverted` — stops the button from changing DPI and sends HIDpp notifications instead
- `dpi 500` — locks DPI at the fast preset

### Raising the default DPI

To raise the mouse speed, change the DPI value in the live system unit and keep the manual bootstrap command consistent:

1. Edit `/etc/systemd/system/mx-ergo-s-setup.service`.
2. Replace `ExecStart=/usr/bin/solaar config "MX Ergo S" dpi 500` with your target value, if you want to change it again later.
3. If you re-run the first-connect bootstrap by hand, use the same DPI value there too.
4. Run `sudo systemctl daemon-reload`.
5. Restart the host service with `sudo systemctl restart mx-ergo-s-setup.service`.
6. Verify with `sudo systemctl status mx-ergo-s-setup.service` or `journalctl -t mx-ergo-s-setup -n 20`.

**trackball-nav hidraw reader** — a background thread opens `/dev/hidraw1`, reads
REPROG_CONTROLS_V4 DivertedButtonsEvent reports (HIDpp LONG report, ID `0x11`, 20 bytes),
and emits `KEY_ENTER` via UInput when CID 253 (DPI Switch) transitions to pressed.

Key constants in the daemon:
```python
DPI_SWITCH_CID       = 253   # from: solaar show "MX Ergo S" → "NamedInt(253, 'DPI Switch')"
REPROG_CTRL_FEAT_IDX = 10    # runtime feature index of REPROG_CONTROLS_V4 (0x1B04)
                              # verify: sudo solaar show "MX Ergo S" | grep -n REPROG
```

If `REPROG_CTRL_FEAT_IDX` changes after a firmware update, update that constant and restart the service.

## Tuning

Thresholds at the top of `executable_trackball-nav`:

```python
SCROLL_STEP      = 20    # ball delta units per scroll notch
WORKSPACE_STEP   = 60    # ball delta units per workspace/window move
APPSWITCH_STEP   = 120   # ball delta units per alt-tab tick
TABSWITCH_STEP   = 120   # ball delta units per ctrl-tab tick
CHORD_WAIT_MS    = 0.300 # double-tilt window for close-window gesture
```

Higher value = less sensitive. Deploy and restart after changes.

## How it works

The daemon grabs the physical evdev device exclusively. Per-button state machine:

- `PENDING` — button held, no action fired yet → release emits a tap click
- `ACTIVE` — an action fired during this hold → release does nothing
- `IDLE` — button not held

Ball movement while a modifier is `PENDING` or `ACTIVE` accumulates into
`accum_x`/`accum_y`. When an accumulator exceeds a step threshold, an action
fires, the accumulator decrements by the step, and the button moves to `ACTIVE`.
REL_X/REL_Y are suppressed while a modifier is held; other axes pass through.

A separate daemon thread reads `/dev/hidraw1` for HIDpp DivertedButtonsEvent
notifications (report ID `0x11`, feature index `REPROG_CTRL_FEAT_IDX`, address
`0x00`). CID transitions from absent to present trigger Enter via UInput.

On evdev disconnect the main loop calls `wait_for_device()` and re-grabs.
The hidraw thread independently retries on error. `Restart=on-failure` handles crashes.
