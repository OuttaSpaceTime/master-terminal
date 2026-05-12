---
title: Claude Code
tags: [claude-code, chezmoi, settings, hooks]
created: 2026-04-11
updated: 2026-04-30
---

# Claude Code

## Managed files

The following `~/.claude/` files are chezmoi-managed (source under `home/dot_claude/`):

| Source | Deployed |
|--------|----------|
| `home/dot_claude/settings.json` | `~/.claude/settings.json` |

Skills are managed separately via symlinks — see [Workspace Skills](workspace-skills.md).

## settings.json drift constraint

Claude Code writes runtime state back into `~/.claude/settings.json` during normal use. Fields known to mutate at runtime:

- `feedbackSurveyState` — session survey timestamp
- `effortLevel` — changed via `/fast` or the UI
- `advisorModel` — changed via the UI
- `voiceEnabled`, `autoDreamEnabled` — toggled in UI

**Do not include these in the chezmoi source.** The current `home/dot_claude/settings.json` intentionally omits `feedbackSurveyState`.

### Workflow for intentional settings changes

1. Edit `home/dot_claude/settings.json` (the source)
2. `chezmoi -S home diff` to preview
3. `chezmoi -S home apply ~/.claude/settings.json` to deploy

### Workflow when Claude Code mutates settings you want to keep

If you change something in the UI (e.g. `advisorModel`) and want to persist it:

1. `chezmoi -S home diff` — review what drifted
2. `chezmoi -S home add ~/.claude/settings.json` — pull deployed file back into source (imports everything including runtime fields)
3. Manually remove runtime-only fields from `home/dot_claude/settings.json` before committing

### Workflow when deployed settings drift and you want to discard it

```bash
chezmoi -S home apply --force ~/.claude/settings.json
```

This overwrites the deployed file with the source, discarding any runtime mutations.

## Global env settings

Claude Code documents `~/.claude/settings.json` as the user-global settings file. Any Claude Code environment variable can be set under the `env` key there to apply it to every session.

For the agent-teams flag, the source file should contain:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Hooks

| Hook event | Action |
|---|---|
| `PostToolUse` (`Edit\|Write\|MultiEdit`) | `chezmoi-guard.sh` — block accidental edits outside `home/` |
