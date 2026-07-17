---
title: Light Theme Color Palette
tags: [kitty, neovim, catppuccin, fzf, fonts, colors, theme, lazygit]
created: 2026-07-15
updated: 2026-07-17
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
| `#3277f5` | blue (AA-large 3.95:1 on `#fafafa`, 4.01:1 vs `#1c1e2a` text) — cursor, url, links, keywords, fzf `hl` |
| `#fa0032` | red (AA-large 3.94:1 on `#fafafa`, 4.03:1 vs `#1c1e2a` text) — errors, diff-removed, fzf `pointer` |
| `#0da04d` | green (AA-large 3.27:1 on `#fafafa`, 4.85:1 vs `#1c1e2a` text) — strings, diff-added, fzf `marker`, p10k branch/versions |
| `#e06100` | orange (AA-large 3.42:1 on `#fafafa`, 4.63:1 vs `#1c1e2a` text) — kitty `color3`, statusline, nvim `yellow`, lazygit `markedBaseCommitBgColor`, p10k (via ANSI 3) |
| `#0f898f` | teal (AA-large 4.03:1 on `#fafafa`, 3.94:1 vs `#1c1e2a` text) — fzf `spinner`, lazygit `searchingActiveBorderColor`, statusline cyan |
| `#dd22ae` | pink / magenta (AA-large 4.09:1 on `#fafafa`, 3.87:1 vs `#1c1e2a` text) — kitty `color5`, statusline magenta |
| `#9e4bec` | mauve (AA-large 4.31:1 on `#fafafa`, 3.68:1 vs `#1c1e2a` text) — nvim keywords |
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

### lazygit
- `home/private_dot_config/lazygit/config.yml` — `gui.theme` (lazygit ships with a
  dark-only default theme, has no light/dark auto-detection). Colors are hex, reused
  from existing roles rather than picked fresh: `activeBorderColor`/
  `inactiveBorderColor` mirror kitty's own `active_border_color`/
  `inactive_border_color`; `selectedLineBgColor` mirrors kitty `selection_background`
  (`#ccd0da`); `cherryPickedCommitFgColor`/`BgColor` reuse the sky+near-black pairing
  (`#74c7ec` / `#11131a`); `markedBaseCommitBgColor` reuses the orange accent
  (`#e06100`) with light text on top. Option names/hex support verified via
  `lazygit -c` (prints the default config) and upstream `docs/Config.md`. Also uses
  `delta --light` for pagers (`git.pagers`). Deploy with
  `chezmoi -S home apply ~/.config/lazygit/config.yml`.

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
