---
title: Bluetooth Audio Toggle
tags: [bluetooth, audio, pipewire, pactl, sony, wh-1000xm5, gnome, hotkey]
created: 2026-04-21
updated: 2026-04-21
---

# Bluetooth Audio Toggle

`Super+Shift+i` toggles the Sony WH-1000XM5 between two Bluetooth profiles.

| Mode | Profile | Use |
|---|---|---|
| Hi-fi | `a2dp-sink` (LDAC ~990 kbps) | Music, no mic |
| Headset | `headset-head-unit-msbc` (mSBC 16 kHz wideband) | Calls, mic on |

Bluetooth classic can only run one profile at a time — LDAC + mic is not possible on this device.

## Chezmoi-managed files

- `home/dot_local/bin/executable_bt-audio-toggle` — the toggle script
- `home/dot_local/bin/executable_apply-gnome-shortcuts` — registers the GNOME custom keybinding (`custom0`)

## How the keybinding is wired

GNOME custom keybindings live at `org.gnome.settings-daemon.plugins.media-keys custom-keybindings`. `apply-gnome-shortcuts` sets three gsettings on `custom0`:

```
name    = "Toggle headset"
command = "$HOME/.local/bin/bt-audio-toggle"
binding = "<Super><Shift>i"
```

`apply-gnome-shortcuts` runs on login via the autostart entry, so the binding survives GNOME resets.

## Why `Super+Shift+i` (not `Super+i`)

Plain `<Super>i` is silently grabbed somewhere outside `dconf` (likely a shell extension). The daemon logs `media-keys-plugin-WARNING: Failed to grab accelerator for keybinding custom:...custom0/` when the combo is already owned. Adding Shift grabs cleanly.

To debug a grab failure:

```bash
kill $(pgrep -f gsd-media-keys); nohup /usr/libexec/gsd-media-keys > /tmp/gsd.log 2>&1 & disown
sleep 2 && grep -iE "failed|grab" /tmp/gsd.log
```

## Codec ceiling

Both profiles are already on the best available codec for the WH-1000XM5 on Linux/PipeWire:

- **Hi-fi**: LDAC is top. AAC isn't listed → PipeWire's AAC codec isn't installed, but LDAC beats it anyway. aptX variants aren't supported by the XM5.
- **Headset**: mSBC wideband is top; the only alternative is CVSD narrowband (worse).

For better call quality on the same hardware there is no software upgrade — it would need Bluetooth LE Audio / LC3, which the XM5 does not support.

## Why phone audio sounds better

1. Sony Headphones Connect app applies DSP (DSEE Extreme, 360 Reality Audio, EQ) on the phone side. Not available on Linux.
2. Phones reliably sustain LDAC 990 kbps; PipeWire's LDAC often negotiates down to 660 or 330 under link stress.
3. iPhone uses Apple's AAC encoder (best-in-class) — Linux doesn't have an equivalent.
4. Phone calls: only the phone↔headset hop is Bluetooth mSBC; the rest of the path is VoLTE/HD Voice. On a PC the whole chain is mSBC.
