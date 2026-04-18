---
title: Chezmoi
tags: [chezmoi, dotfiles]
created: 2026-04-07
updated: 2026-04-09
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
