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
| `home/dot_claude/executable_notify.sh` | `~/.claude/notify.sh` |
| `home/dot_claude/executable_set-tab-icon.sh` | `~/.claude/set-tab-icon.sh` |
| `home/dot_claude/executable_test-tab-icon.sh` | `~/.claude/test-tab-icon.sh` |

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

`~/.claude/settings.json` only keeps the `PostToolUse` chezmoi guard hook now. Kitty tab state is handled by the `claude()` shell wrapper instead of Claude Code hooks:

| Hook event | Action |
|---|---|
| `PostToolUse` (`Edit\|Write\|MultiEdit`) | `chezmoi-guard.sh` — block accidental edits outside `home/` |

## Tab icons

`set-tab-icon.sh` prepends a state icon to the kitty tab title without overwriting it. Manual tab renames (Ctrl+Shift+Alt+T) are always preserved — the script reads the current title from `kitty @ ls` on every state change and strips/re-applies the icon prefix.

Active use is currently limited to the `claude()` shell wrapper, which sets the running state on start and clears it on exit. The script still supports `permission` and `finished`, but those states are no longer driven by Claude Code hooks in this repo.

### States

| Icon | State | Trigger |
|------|-------|---------|
| ⚡️ | Running | `claude()` wrapper |
| ❓️ | Needs permission/input | supported by script, not currently hooked |
| ✅ | Finished | supported by script, not currently hooked |

### Multi-split behavior

When multiple Claude sessions run as splits in the same kitty tab, all distinct state icons are shown in priority order. Examples:

- One running + one finished → `⚡️✅ master`
- One needs permission + one running → `❓️⚡️ master`
- Both running → `⚡️ master` (deduplicated)

The script discovers sibling windows via the same `kitty @ ls` call it uses to read the tab title (no extra IPC). Only windows with state files in `/tmp/claude-tab-state/` are considered — non-Claude splits are ignored.

### Lifecycle

1. The `claude()` zsh wrapper calls `set-tab-icon.sh running` on entry
2. The wrapper runs `direnv allow .` quietly before launching Claude so the current project stays authorized
3. The wrapper is the only place that updates kitty tab state during a normal session
4. On exit (normal or signal), the wrapper calls `set-tab-icon.sh clear` which strips the icon prefix and removes the state file
5. If no state files exist (not in kitty, or session started before the wrapper), the script is a silent no-op

### Testing

Run `~/.claude/test-tab-icon.sh` in a kitty tab with at least one split to exercise all cases (single session, multi-split priority, redundancy skip, manual rename, clear, non-kitty).
