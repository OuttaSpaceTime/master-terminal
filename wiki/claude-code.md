---
title: Claude Code
tags: [claude-code, chezmoi, settings, hooks]
created: 2026-04-11
updated: 2026-09-01
---

# Claude Code

## Managed files

The following `~/.claude/` files are chezmoi-managed (source under `home/dot_claude/`):

| Source | Deployed |
|--------|----------|
| `home/dot_claude/modify_settings.json` | `~/.claude/settings.json` (merge script, see below) |

Skills are managed separately via symlinks — see [Workspace Skills](workspace-skills.md).

## settings.json is merged, not overwritten

Claude Code writes UI state back into `~/.claude/settings.json` during normal use — `/config` toggles, `/model`, theme, output style — so a plain chezmoi-managed file drifted after almost every session. Since 2026-09-01 the source is a chezmoi **`modify_` script** instead: chezmoi feeds it the current contents of the deployed file on stdin and takes its stdout as the target contents (chezmoi reference, [target types](https://www.chezmoi.io/reference/target-types/): *"The script receives the current contents of the target file on standard input and must write the new contents to standard output."*).

`home/dot_claude/modify_settings.json` holds two JSON blobs and merges them over the live file, preserving the live key order:

- **`MANAGED`** — repo wins, overwritten on every apply: `$schema`, `permissions`, `hooks`, `statusLine`, `enabledPlugins`.
- **`DEFAULTS`** — live wins; filled in only when the deployed file lacks the key: `model`, `outputStyle`, `effortLevel`, `theme`, `tui`, `verbose`, `voiceEnabled`, `autoDreamEnabled`, `promptSuggestionEnabled`, `preferredNotifChannel`, `skipDangerousModePermissionPrompt`, `skipWorkflowUsageWarning`, `skipAutoPermissionPrompt`.

Any key in neither blob (a new Claude Code setting, `feedbackSurveyState`, …) passes through untouched, so nothing needs stripping any more. The result: **`chezmoi -S home diff` stays empty no matter what you toggle in the UI**, while hooks and permissions stay enforced from the repo.

The source file needs no executable bit (verified: chezmoi runs it at mode `644`).

### Workflows

- **Change a hook, permission, statusline or plugin:** edit the `MANAGED` blob, then `chezmoi -S home apply ~/.claude/settings.json`.
- **Change a UI preference:** just change it in Claude Code. Nothing to sync — it survives every apply.
- **Change what a *fresh machine* starts with:** edit `DEFAULTS`. This does not affect a machine where the key is already set.
- **Force a UI key on every machine:** move it from `DEFAULTS` to `MANAGED`.
- `chezmoi re-add` / `chezmoi add` no longer apply to this file — the source is a script, not a copy. There is nothing to re-capture.

Tests: `tests/test_claude_settings_modify.py` (`uv run pytest`).

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
