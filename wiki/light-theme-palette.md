---
title: Light Theme Color Palette
tags: [kitty, neovim, catppuccin, fzf, fonts, colors, theme]
created: 2026-07-15
updated: 2026-07-15
---

# Light Theme Color Palette

A soft near-white, high-contrast light theme across kitty, Neovim
(catppuccin-latte), the Claude Code statusline/diffs, and fzf. Base is neutral
near-white; text is near-black; accents are deepened/saturated so they pop on white.

## Font

**JetBrainsMono Nerd Font**, styles **SemiBold** (regular) / **ExtraBold** (bold) —
a heavy weight so text and syntax colors pop on white (the previous `MesloLGS NF`
had only Regular/Bold and looked thin). Set in `kitty.conf` via the
`family="..." style="..."` syntax; nvim and Claude Code inherit the terminal font.
Installed to `~/.local/share/fonts/JetBrainsMonoNF/`
(see `.solve/tasks/2026-07-15-install-jetbrains-nf/`). To go thicker: raise
`font_size` (currently 9), switch regular to `Bold`, or add a fontconfig
`embolden` rule (synthetic, stacks on any weight).

## Core palette

| Hex | Role |
|-----|------|
| `#fafafa` | background — kitty bg, nvim base/mantle, `tab_bar_background` |
| `#f0f0f2` | crust / secondary surface |
| `#1c1e2a` | primary text (near-black) |
| `#2c2e40` | secondary text / ANSI color0 |
| `#3c3f54` | tertiary text (subtext0) |
| `#0a4fd0` | blue — cursor, url, links, keywords, fzf `hl` |
| `#bd0026` | red — errors, diff-removed, fzf `pointer` |
| `#0f6e2a` | green (forest) — strings, diff-added, fzf `marker`, p10k branch/versions |
| `#9a6700` | yellow / amber |
| `#0c6e74` | teal |
| `#c81f9e` | pink / magenta |
| `#9333ea` | mauve — nvim keywords |
| `#74c7ec` | sky — kitty active tab bg (pair with black text `#11131a`) |

## Where each color lives

Edit the chezmoi **source**, then `chezmoi -S home apply <target>`.

### kitty
- `home/private_dot_config/kitty/current-theme.conf` — `background`, `foreground`,
  `cursor`, `url_color`, `selection_*`, ANSI `color0`–`color17`.
- `home/private_dot_config/kitty/kitty.conf` — fonts + tab colors (`active_tab_*`,
  `inactive_tab_*`, `tab_bar_background`). The tab lines here **override** the theme
  file's tab lines. Reload kitty with `ctrl+shift+F5`.

### Neovim (catppuccin-latte)
- `.../nvim/lua/plugins/colorscheme.lua` — `color_overrides.latte` redefines
  base/mantle/crust/text/subtext and every accent. Single place to retune syntax.
  Restart nvim to apply.
- `.../nvim/lua/config/autocmds.lua` — `kitty_bg_sync` augroup: OSC-11 sync sets
  kitty's bg to nvim's `Normal` on enter, restores on exit (removes the edge border).
- `.../nvim/lua/plugins/snacks-picker.lua` — disables the `default` picker backdrop.

### Claude Code
- `home/dot_claude/statusline-script.sh` — statusline colors (managed), truecolor
  (`\033[38;2;R;G;Bm`) matching the exact palette hex.
- `home/dot_claude/themes/light-high-contrast.json` — diff colors (`diffAdded`/
  `diffRemoved`/word tokens); base `light`. Activate via `/theme`.

### zsh / fzf / prompt
- `home/dot_zshrc` — `FZF_DEFAULT_OPTS` `--color` (fzf + fzf-tab overlay) and
  `ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE`. Reopen the shell to apply.
- `home/dot_p10k.zsh` — powerlevel10k prompt (managed). Uses **basic ANSI codes**
  (1-7) for segments and inside `my_git_formatter` (e.g. `clean='%2F'`), so it
  inherits the kitty ANSI palette (`color1-6`) automatically — no per-color theming
  needed. Icons: set to **few** (branch icon + VCS/exec-time visual identifiers
  emptied); `p10k configure`'s "many icons" re-adds them.

## Gotchas (hard-won)

- **Grey frame around nvim** had two independent causes: (1) kitty bg ≠ nvim
  `Normal` → the cell-grid edge gap shows kitty's bg (fixed by the OSC-11 autocmd);
  (2) the Snacks `default` picker layout was the only one without `backdrop = false`
  — its black scrim renders grey on a light bg.
- **"Brownish" cast** = catppuccin rosewater `#dc8a78` (a tan) on cursor/selection/url.
- **Thin strips below the statusline / kitty tab bar** = grey `tab_bar_background`
  seam; set it equal to `background`.
- **Ground-truth probe** instead of guessing from screenshots: query the running
  nvim via its `--server` socket
  (`synIDattr(synIDtrans(hlID("Normal")),"bg#")`, plus `NormalFloat`, window list)
  and kitty via `kitten @ --to unix:/tmp/kitty-<pid> get-colors`. Reusable script at
  `.solve/tasks/2026-07-14-probe-nvim-colors/`.
- **p10k branch/git colors** live in `my_git_formatter()` (`clean`/`modified`/
  `untracked`/`conflicted`), NOT the `POWERLEVEL9K_VCS_*_FOREGROUND` vars. The current
  config uses ANSI codes (`%2F` …) that follow the kitty palette; `%F{#hex}` also works.
- **`p10k configure` regenerates the whole file** — resets colors to ANSI and may
  re-add icons (os_icon segment, `VCS_BRANCH_ICON`, per-segment visual identifiers).
  After running it: `chezmoi add ~/.p10k.zsh`, then re-check colors + strip icons.
- Stale nvim/kitty instances (and long-running shells) keep their old colors —
  restart them / `source ~/.p10k.zsh`; don't trust old windows.
