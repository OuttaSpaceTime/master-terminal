---
title: Workspace Skills
tags: [skills, agents, chezmoi]
created: 2026-04-08
updated: 2026-04-09
---

# Workspace Skills

## Commands

- `agent-skills-sync --dry-run` — preview workspace skill sync changes
- `agent-skills-sync --apply` — sync workspace skill changes into home directory
- `agent-skills-import-claude <skill> --dry-run` — preview a Claude skill import
- `agent-skills-import-claude <skill> --apply` — import a Claude skill into the managed tree

## Shared Skill Symlinks

The canonical workspace-local skill tree lives in `home/dot_agents/skills/`. Both Claude (`~/.claude/skills`) and Codex (`~/.codex/skills`) point at the same shared tree (`~/.agents/skills`) via chezmoi symlinks.

- `home/dot_claude/skills/` and `home/dot_codex/skills/` contain chezmoi `symlink_*` entries
- This avoids duplicating skill content across clients
- `dot-manage` is the workspace-local skill for coordinating dotfile, skill, and wiki updates
