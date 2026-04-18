---
title: Sofle Keyboard
tags: [keyboard, sofle, keebart, vial, qmk]
created: 2026-04-14
updated: 2026-04-14
---

# Sofle Keyboard

Model: **Keebart Sofle Choc Pro** (wired, no encoders — keys in encoder positions instead).

## Firmware & remapping

- Runs **QMK** with **Vial** support
- Remap via [get.vial.today](https://get.vial.today) (Chrome/Edge, needs WebHID)
- Changes save to onboard memory — persist across machines, no flashing needed
- Keebart's Vial-QMK fork (`Keebart/vial-qmk-sofle-choc-pro`) was archived Feb 2026 — check [keebart.com](https://www.keebart.com) for firmware updates

## Linux setup

If the browser doesn't detect the board, add a udev rule:

```bash
sudo tee /etc/udev/rules.d/50-vial.rules << 'EOF'
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{serial}=="*vial:f64c2b3c*", MODE="0660", GROUP="users", TAG+="uaccess", TAG+="udev-acl"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Then unplug and replug.

## Layout decisions

_Track keymap choices here as the layout evolves._

### Layers

| Layer | Purpose | Notes |
|-------|---------|-------|
| 0 | Alpha + base mods | Default QWERTY (or swap to Colemak etc.) |
| 1 | Navigation + numbers | |
| 2 | Symbols + F-keys | |
| 3 | Media + board settings | |

### Thumb cluster

No encoders — all keys. The thumb keys are the highest-value positions on the board.

_Record thumb assignments here once settled._

### Home row mods

Not yet configured. Recommended to wait until comfortable with the physical layout before adding hold-tap behaviour.
