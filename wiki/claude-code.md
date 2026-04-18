---
title: Claude Code
tags: [claude-code, chezmoi, settings, hooks]
created: 2026-04-11
updated: 2026-04-14
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

## Hooks

`~/.claude/settings.json` configures hooks that fire during a Claude session:

| Hook event | Action |
|---|---|
| `PreToolUse` | `set-tab-icon.sh running` — set ⚡️ icon |
| `Notification` (`permission_prompt\|elicitation_dialog`) | `set-tab-icon.sh permission` — set ❓️ icon |
| `Stop` | `notify-send` desktop notification + `set-tab-icon.sh finished` — set ✅ icon |

## Tab icons

`set-tab-icon.sh` prepends a state icon to the kitty tab title without overwriting it. Manual tab renames (Ctrl+Shift+Alt+T) are always preserved — the script reads the current title from `kitty @ ls` on every state change and strips/re-applies the icon prefix.

### States

| Icon | State | Trigger |
|------|-------|---------|
| ⚡️ | Running | `PreToolUse` hook |
| ❓️ | Needs permission/input | `Notification` hook |
| ✅ | Finished | `Stop` hook |

### Multi-split behavior

When multiple Claude sessions run as splits in the same kitty tab, all distinct state icons are shown in priority order. Examples:

- One running + one finished → `⚡️✅ master`
- One needs permission + one running → `❓️⚡️ master`
- Both running → `⚡️ master` (deduplicated)

The script discovers sibling windows via the same `kitty @ ls` call it uses to read the tab title (no extra IPC). Only windows with state files in `/tmp/claude-tab-state/` are considered — non-Claude splits are ignored.

### Lifecycle

1. The `claude()` zsh wrapper calls `set-tab-icon.sh running` on entry
2. Claude Code hooks update the icon during the session
3. Redundant `PreToolUse` calls are skipped (state file comparison, no `kitty @` call)
4. On exit (normal or signal), the wrapper calls `set-tab-icon.sh clear` which strips the icon prefix and removes the state file
5. If no state files exist (not in kitty, or session started before the wrapper), the script is a silent no-op

### Testing

Run `~/.claude/test-tab-icon.sh` in a kitty tab with at least one split to exercise all cases (single session, multi-split priority, redundancy skip, manual rename, clear, non-kitty).
