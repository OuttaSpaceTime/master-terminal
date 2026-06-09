---
title: Kitty
tags: [kitty, terminal]
created: 2026-04-07
updated: 2026-05-20
---

# Kitty

## Update

- This machine uses the official binary install: `kitty 0.46.0` at `~/.local/kitty.app`
- Update it by re-running the installer:

```bash
curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
```

- Kitty’s own update check only applies to official binary builds; distro packages do not use it

## Shortcuts

- `Ctrl+Shift+T` — new window
- `Ctrl+Shift+Enter` — new split
- `Ctrl+Shift+,` — move the active tab left within the current kitty window
- `Ctrl+Shift+.` — move the active tab right within the current kitty window
- `Ctrl+Shift+[` / `Ctrl+Shift+]` — switch between splits
- `Ctrl+Shift+W` — close current split (or tab if only split)
- `Ctrl+Shift+F5` — reload kitty config
- `Ctrl+A` — jump to beginning of input line (readline/zsh)
- `Ctrl+E` — jump to end of input line (readline/zsh)
- `Ctrl+Alt+H` / `Ctrl+Alt+L` — previous / next tab
- `Ctrl+Alt+K` — clear the current terminal screen
- `Ctrl+Shift+Alt+T` — rename current tab
- `kitten @ set-tab-title "New Name"` — rename tab from CLI

## Line Editing

These are the usual readline/zsh-style shortcuts for editing commands in the prompt:

- `Alt+F` — move forward one word
- `Alt+B` — move back one word
- `Ctrl+A` — jump to the start of the line
- `Ctrl+E` — jump to the end of the line
- `Alt+D` — delete the next word
- `Ctrl+W` — delete the previous word
- `Ctrl+R` — search shell history interactively

## Scrolling (Keyboard)

Kitty default scroll bindings use `kitty_mod` (`Ctrl+Shift` by default):

- `Ctrl+Shift+↑` / `Ctrl+Shift+↓` — scroll by line
- `Ctrl+Shift+PageUp` / `Ctrl+Shift+PageDown` — scroll by page
- `Shift+Alt+Up` / `Shift+Alt+Down` — scroll by half a page
- `Ctrl+Shift+Home` / `Ctrl+Shift+End` — scroll to top / bottom
- `Ctrl+Shift+Z` / `Ctrl+Shift+X` — jump to previous / next shell prompt (requires shell integration)

This repo also binds kitty-scrollback.nvim for vim-style browsing:

- `Ctrl+Shift+H` — open full scrollback buffer in nvim (`kitty.conf:78`)
- `Ctrl+Shift+G` — open last command's output in nvim (`kitty.conf:80`)
- Inside the nvim pager: normal motions (`j/k`, `Ctrl+U`/`Ctrl+D`, `gg`/`G`, `/` to search)

## Copy On Select

- `copy_on_select yes` copies selected text to the clipboard automatically
- `strip_trailing_spaces smart` strips trailing whitespace from copied selections so pasted commands don't carry extra line breaks from terminal line-wrapping
  - Values: `never` (default, keeps everything), `smart` (strip on normal selections, preserve in rectangle selections), `always` (strip on both)
  - Rectangle selection in kitty: hold `Ctrl+Alt` while dragging — selects a block instead of flowing line-by-line, useful for grabbing aligned columns where padding spaces matter
  - Stripping only affects the clipboard contents, not the visual highlight — the selection overlay still covers the whitespace
  - Only trailing whitespace (between the last non-space character and the newline) is removed; leading whitespace and inter-word spaces are preserved

## Sessions

- `F7` — save session (prompts for name, saves under `~/.local/share/kitty/sessions`)
- `F8` — restore/switch sessions (only shows files with recognized session extension)
- Plain names like `test` without the session extension won't appear in F8

## Tab Titles

- `kitty @ set-tab-title` is what the shell uses to rename the active tab
- `home/dot_zshrc` auto-updates kitty tab and window titles from the prompt and from `codex`/`claude` command wrappers
- `shell_integration enabled no-title` prevents kitty shell integration from changing titles based on the running foreground command
- `tab_title_template "{title}"` lets the tab bar show restored/manual tab titles from sessions instead of forcing a numeric index

## Moving And Reordering Tabs

- Within the current kitty window, use `Ctrl+Shift+,` and `Ctrl+Shift+.` to move the active tab left or right
- You can also drag tabs in the tab bar to reorder them manually
- `Ctrl+1` through `Ctrl+9` jump directly to tab 1 through 9 in this repo's kitty config

## Moving A Window Back Into Another OS Window As A Tab

- Kitty calls this action `detach_window`
- In this repo's kitty config, `Ctrl+F2` moves the current window into the previously active tab
- In this repo's kitty config, `Ctrl+F3` moves the current window into a new tab
- In this repo's kitty config, `Ctrl+F4` prompts for a target tab or window
- Recent kitty versions also let you drag a tab in the tab bar between OS windows
