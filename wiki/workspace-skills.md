---
title: Workspace Skills
tags: [skills, agents, chezmoi]
created: 2026-04-08
updated: 2026-06-08
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

## Solveit Nvim

- `solveit-nvim` guides ordinary Nvim project work through Polya micro-steps: understand the problem, devise a plan, carry out the plan, look back
- On startup it creates `.claude/notes/<YYYY-MM-DD>-<task-slug>.md` with the four Polya headings, commits a private `.claude/notes` Git baseline, then prints `nvim-listen <path>` so the note becomes the shared cockpit
- It uses Git baselines for review markers: scratch notes are committed only inside the private nested repo; main-repo WIP commits are allowed only on non-main branches and only for approved agent scope
- Agent edit batches stop after 8 changed lines so the next dirty lines remain easy to inspect with LazyVim/Gitsigns
- It is coaching-only by default: no direct probe commands, code suggestions, self-run probes, or edits unless the user explicitly asks
- When the user asks for suggestions, it gives one smallest viable probe or code suggestion, then stops for user verification
- The user owns conclusions: after evidence lands, the skill asks what conclusion the user draws instead of synthesizing the full answer, recommendation, or decision tree
- It starts in manual context mode and can use higher Nvim integration levels when available: selection push, ambient pull, guided steering
- It has an explicit edit lock: investigation and patch contracts first, no file edits until the user approves the exact scope
