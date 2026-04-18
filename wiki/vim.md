---
title: Vim
tags: [vim, clipboard, editor]
created: 2026-04-09
updated: 2026-04-09
---

# Vim

## Clipboard

- `home/dot_vimrc` configures `vim` to use `unnamedplus` when supported
- On this machine's `vim` binary, clipboard support is missing, so the config falls back to `wl-copy`, then `xclip`, then `xsel`
- Normal yanks, deletes, and changes are copied to the system clipboard through `TextYankPost`
- In Vim, `+` is still the normal next-line motion
- Wayland clipboard helpers are available:
  - `wl-copy`
  - `xclip`
  - `xsel`
