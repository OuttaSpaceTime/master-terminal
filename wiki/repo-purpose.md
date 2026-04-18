---
title: Repo Purpose
tags: [meta, structure]
created: 2026-04-07
updated: 2026-04-09
---

# Repo Purpose

This repo has three jobs:

1. **Chezmoi source tree** — terminal and editor configuration under `home/`
2. **Agent skill tree** — workspace-local skill definitions under `home/dot_agents/skills/`
3. **Local wiki** — repo-specific workflow notes under `wiki/`

## Structure

- `home/` — operational dotfiles managed through chezmoi
- `home/dot_agents/skills/` — workspace-local agent skill definitions
- `wiki/` — topic-per-file notes for repo-specific knowledge

## Boundaries

- Keep operational config in `home/`
- Keep workspace-local skills in `home/dot_agents/skills/`
- Keep only repo-specific lookup notes in `wiki/`
- `~/Code/Misc/wiki` is outside this repo's retrieval flow
