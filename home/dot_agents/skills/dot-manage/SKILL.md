---
name: dot-manage
description: >
  Global skill for managing agent skills, dotfiles, and minimal local wiki documentation in
  master-terminal. Use from any directory to create or update skills (invokes skill-creator
  when needed), apply chezmoi changes, update repo-specific wiki docs, or inspect home/ config.
  Trigger on: "create a skill", "update this skill", "add this to my dotfiles", "document this
  in the wiki", "sync skills", or any request that touches ~/.agents/skills, chezmoi, or the
  master-terminal wiki.
---

# Dot Manage

Global orchestration skill for the master-terminal dotfiles repo. Works from any directory.

## Fixed Paths

- **Repo root:** `~/Code/Misc/master-terminal`
- **Chezmoi source:** `~/Code/Misc/master-terminal/home`
- **Skill source tree:** `~/Code/Misc/master-terminal/home/dot_agents/skills/`
- **Deployed skills:** `~/.agents/skills/`
- **Local wiki:** `~/Code/Misc/master-terminal/wiki/`
- **External wiki destination:** `~/Code/Misc/wiki/`

Always read `AGENTS.md` and `wiki/index.md` before deciding how to route a non-trivial request.

## Operating Rules

- Treat `home/` as the operational source of truth for config and skills
- Treat `wiki/` as a minimal local memory for repo-specific answers the user actually asked for
- Never read from `~/Code/Misc/wiki/` as part of this repo's workflow
- Prefer updating existing local wiki pages over creating new ones
- Keep wiki updates tied to real user asks or validated task outcomes
- Use `chezmoi --source ~/Code/Misc/master-terminal/home diff` before applying changes
- Use `chezmoi --source ~/Code/Misc/master-terminal/home apply --force ~/.agents/skills` after skill changes
- Use `chezmoi --source ~/Code/Misc/master-terminal/home apply --force` for broader dotfile changes

## Skill Management

### Creating a new skill

1. Invoke `/skill-creator` to design and draft the `SKILL.md`
2. Write the skill directory to `~/Code/Misc/master-terminal/home/dot_agents/skills/<name>/SKILL.md`
3. Add chezmoi symlinks for both Claude and Codex:
   - `home/dot_claude/skills/symlink_<name>` — contents: `../../.agents/skills/<name>`
   - `home/dot_codex/skills/symlink_<name>` — contents: `../../.agents/skills/<name>`
4. Apply: `chezmoi --source ~/Code/Misc/master-terminal/home apply --force ~/.agents/skills ~/.claude/skills ~/.codex/skills`
5. Update the local wiki only if the skill change creates durable repo-specific behavior worth rediscovering

### Updating an existing skill

1. Read the current skill from `~/Code/Misc/master-terminal/home/dot_agents/skills/<name>/SKILL.md`
2. If the change is significant (new section, new philosophy, structural rewrite) -> invoke `/skill-creator` for the update pass
3. If the change is targeted (fix a rule, add a bullet, sync a principle) -> edit directly
4. Apply: `chezmoi --source ~/Code/Misc/master-terminal/home apply --force ~/.agents/skills`
5. Update the local wiki only when the change affects durable repo-specific workflow behavior

### Syncing interactive principles

When `interactive-principles.md` changes, or when a skill's inline constraints drift from the standard block:

- Edit the canonical source: `home/dot_agents/skills/references/interactive-principles.md`
- Each interactive skill has a chezmoi symlink (`symlink_interactive-principles.md`) in its `references/` dir that points to the canonical copy — no manual copying needed
- Verify every interactive skill has the `## Interactive Constraints (mandatory)` block inline; the interactive skills are the ones with `references/symlink_interactive-principles.md` (`ls home/dot_agents/skills/*/references/symlink_interactive-principles.md`)
- Deploy via `chezmoi -S home apply --force ~/.agents/skills`

### Shared reference symlink convention

Shared reference files live in `home/dot_agents/skills/references/`. Skills reference them as `references/<name>.md` (local to the skill folder). The link is a chezmoi symlink file:
- Source: `home/dot_agents/skills/<skill>/references/symlink_<name>.md` containing `../../references/<name>.md`
- Deployed: `~/.agents/skills/<skill>/references/<name>.md` → `../../references/<name>.md`

When adding a new shared reference or when a skill newly needs one, create the `symlink_<name>.md` file in the skill's `references/` directory.

### Interactive skills requiring the constraints block

Derive the list instead of keeping one here: `ls home/dot_agents/skills/*/references/symlink_interactive-principles.md`

## Dotfile Management

- For kitty/nvim/zsh changes: use `chezmoi --source ~/Code/Misc/master-terminal/home edit <target>` then apply
- Always diff before applying broader dotfile changes
- Keep durable repo-specific adjustments discoverable in the local wiki

## Local Wiki Documentation

Follow the Query Workflow and page format in the repo's `AGENTS.md` ("Working With The Local Wiki"):
check the matching page first, verify it against `home/` and (for anything that changes upstream)
authoritative sources, escalate to `wiki-scout` / `wiki-researcher` only on a miss, and record the
end state with its gotchas, rejected approaches and upstream links.

If the work also produces general knowledge or reflection material worth keeping, write it to `~/Code/Misc/wiki/` separately, but never use that location as a source during normal repo work.

## When to Invoke skill-creator

- Creating any new skill from scratch
- Major structural rewrites of an existing skill
- When the user asks to "improve" or "rethink" a skill, not just patch it

For targeted patches (add a rule, fix wording, sync a principle) -> edit directly without `skill-creator`.

## Workflow

1. Identify the request surface: skill management, dotfiles, local wiki, or chezmoi sync
2. Read `AGENTS.md` and relevant local wiki pages if the request is non-trivial
3. For skill work: create or update in `home/dot_agents/skills/`, then apply via chezmoi
4. For dotfile work: edit through chezmoi-managed files under `home/`, diff, then apply
5. For local wiki work: grep existing topics, inspect repo files, extend or create a topic file, update `wiki/index.md` when files change

## Current Managed Surfaces

- `home/dot_agents/skills/` — agent skill source tree
- `home/dot_claude/skills/` — Claude symlinks
- `home/dot_codex/skills/` — Codex symlinks
- `home/private_dot_config/kitty/`
- `home/private_dot_config/nvim/`
- `home/dot_zshrc`
- `wiki/`

## Related

- [Wiki Index](../../../../wiki/index.md)
