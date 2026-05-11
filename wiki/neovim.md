---
title: Neovim and LazyVim
tags: [neovim, lazyvim, editor]
created: 2026-04-07
updated: 2026-05-07
---

# Neovim and LazyVim

## Shortcuts

- `Ctrl+W h/j/k/l` — move between splits
- `Ctrl+W =` — equalize split sizes
- `Space+F+F` — find files
- `Space+S+G` — grep text
- `Space+S+B` — grep current buffer (picker)
- `/` — search current buffer (built-in, incremental); `n`/`N` to cycle matches
- `Space+S+R` — resume last picker state
- `Space+G+S` — open changed files
- `Space+G+D` — grouped git diff picker
- `]f` / `[f` — jump to next/previous function start
- `]F` / `[F` — jump to next/previous function end
- `]c` / `[c` — jump to next/previous class start
- `]C` / `[C` — jump to next/previous class end
- `]a` / `[a` — jump to next/previous parameter start
- `]A` / `[A` — jump to next/previous parameter end
- `]h` — jump to the next git hunk in the current buffer
- `[h` — jump to the previous git hunk in the current buffer
- `Ctrl+/` — floating terminal
- `Space+l` or `:Lazy` — open the Lazy.nvim plugin manager UI; press `q` to close

## Search and Replace Across Project

- `Space+s+r` — open [spectre.nvim](https://github.com/nvim-pack/nvim-spectre) for project-wide find & replace
  - Inside spectre: `<leader>R` applies all, or use the header actions `\r` (replace current), `\s` (sync all), `\l` (sync line), `\n` (sync next)
  - Scope with the **Files Filter** (globs like `*.rb`) and **Paths** fields (e.g. `./app/models/`)

## Buffers

- `Space+b+d` — close the current buffer
- `Space+b+p` — pin the current buffer
- `Space+b+P` — delete all buffers except pinned ones
- `:bufdo bd` — close all listed buffers
- `:2,5bd` — close a specific range of buffer numbers

## Ruby / RuboCop

- RuboCop is not Mason-managed in this config; `mason = false` is set for the Ruby servers
- Ruby LSP owns RuboCop in this config with `formatter = "rubocop"` and `linters = { "rubocop" }`
- That means the project’s `Gemfile` / `Gemfile.lock` decides the RuboCop version, not a global Mason install
- Ruby LSP’s RuboCop integration runs in-process, so it avoids RuboCop server mode
- After changing RuboCop in the bundle, restart the LSP or Neovim to avoid stale LSP processes
- `ruby_lsp` is started via `rbenv exec ruby-lsp`, so it follows the Ruby version selected by `rbenv`

## Indentation

- `gg=G` — re-indent entire file (auto-indent)
- `=` in visual mode — re-indent selection
- `>>` / `<<` — indent/unindent current line
- `>` / `<` in visual mode — indent/unindent selection
- `Space+c+f` — format file with LSP/formatter (respects project config, e.g. prettier, black)

## LazyGit (`Space+g+g`)

### Branch multi-select and bulk delete

- `<Ctrl+Space>` — mark/unmark the branch under the cursor
- `v` then `j`/`k` — range-select a contiguous block of branches
- `d` — delete all marked branches (prompts for force-delete if any are unmerged)
- `<Space>` in the branch panel **checks out** the branch (not a mark key)

### Syntax-highlighted diffs (delta)

Diffs in LazyGit use [delta](https://github.com/dandavtimer/delta) as the pager for language-aware syntax highlighting. Configured in `~/.config/lazygit/config.yml` (chezmoi-managed):

```yaml
git:
  paging:
    colorArg: always
    pager: delta --dark --paging=never
```

## Clipboard

- System clipboard support is available, but `clipboard` is not set globally in this config
- Yank selected text to the system clipboard with `"+y`
- Yank the current line to the system clipboard with `"+yy`
- Paste from the system clipboard with `"+p`
- Custom mappings:
  - `Space+f+y` copies the current file path relative to repo root
  - `Space+f+Y` copies the current file path plus the current line number
