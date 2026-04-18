---
title: Agent File Access
tags: [ai-agents, claude-code, codex, security, secrets]
created: 2026-04-13
updated: 2026-04-13
---

# Agent File Access

## Short answer

If you need a hard guarantee that a coding agent cannot read a file, the reliable solution is still to remove that file from the agent's reachable workspace or enforce the boundary at the OS/container/sandbox level.

Tool-native ignore files are commonly used, but many of them are aimed at indexing or context selection rather than hard filesystem denial.

## Current patterns in use

- **Claude Code deny rules**: Anthropic documents `permissions.deny` rules such as `Read(./.env)` and `Read(./secrets/**)`. These deny reads and exclude matching files from discovery/search.
- **Claude Code hooks**: Anthropic also supports `PreToolUse` hooks that can deny tool calls at runtime, including MCP tool calls.
- **Workspace or branch isolation**: OpenAI positions Codex around folder/branch/workspace sandboxing rather than per-file deny rules. The robust pattern is to keep sensitive files outside the mounted workspace.
- **Indexing ignores**: Continue (`.continueignore`) and Windsurf (`.codeiumignore`) both expose ignore files primarily for indexing/context control.
- **Secret injection wrappers**: Community tooling such as `nopeek` loads env vars into Claude Code sessions without printing values, then adds redaction hooks as a backup.
- **Agent gateways / policy layers**: Platforms such as Stacklok focus on policy enforcement, approved tool access, and running context/tool infrastructure inside controlled environments.

## Practical implication

There is a meaningful difference between:

1. files that are not indexed or not auto-selected for context
2. files the agent is actually forbidden from reading

For sensitive material, prefer hard boundaries first, then tool-native deny rules, then ignore/indexing controls as a weaker convenience layer.

## Sources

- Anthropic Claude Code settings: `permissions.deny` for sensitive files
- Anthropic Claude Code IAM/team docs: permission rules and hooks precedence
- Anthropic Claude Code hooks docs: `PreToolUse` denial and MCP matching
- OpenAI Codex app and Codex product pages: workspace/sandbox boundaries
- Continue docs: `.continueignore`
- Windsurf docs: `.codeiumignore`
- Scott Spence: `nopeek`
- Stacklok platform docs
