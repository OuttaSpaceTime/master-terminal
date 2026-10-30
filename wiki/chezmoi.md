---
title: Chezmoi
tags: [chezmoi, dotfiles]
created: 2026-04-07
updated: 2026-10-30
---

# Chezmoi

## Commands

- `chezmoi -S home diff` — check managed changes before apply
- `chezmoi -S home apply` — sync managed files into `$HOME`
- `chezmoi -S home edit <target>` — edit a managed target

## Decisions

- This repo expects a global `chezmoi` binary
- `chezmoi -S home diff` is the default pre-apply check
- `kitty`, `nvim`, and workspace skill changes must go through files under `home/`
- Some managed files (e.g. `~/.claude/settings.json`) are mutated at runtime by their applications — omit runtime-only fields from the chezmoi source; see [Claude Code](claude-code.md) for the full list and sync workflows
- Secrets stay out of `dot_zshrc`: it sources the unmanaged `~/.zshrc.local` (e.g. `VILOCIFY_API_TOKEN`), which you recreate by hand on a new machine
- Shell aliases and helper functions live in `~/Code/Misc/agentic-setup/shell/aliases.zsh`, sourced from `dot_zshrc`; that repo also holds the Vilocify project-level agent setup and its `restore.sh`
