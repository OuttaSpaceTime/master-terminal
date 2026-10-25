---
title: Claude Code + Neovim Integration
tags: [claude-code, neovim, lazyvim, integration]
created: 2026-04-21
updated: 2026-10-25
---

# Claude Code + Neovim Integration

Running Claude Code in a kitty pane next to nvim (LazyVim) produces two distinct problems with different
solutions. Keep them separate:

1. **Reload**: nvim does not pick up file changes Claude makes on disk. A local nvim concern.
2. **Control / forwarding**: Claude cannot see or steer nvim state. An IPC concern over nvim's msgpack-RPC socket.

## Current setup

### Reload

Autocmd group `auto_checktime` in `home/private_dot_config/nvim/lua/config/autocmds.lua`:

- `FocusGained`, `BufEnter`, `CursorHold`, `CursorHoldI`, `TermLeave` run `pcall(vim.cmd, "checktime")`,
  guarded by `vim.fn.getcmdwintype() == "" and vim.bo.buftype ~= "nofile"`.
- `FileChangedShellPost` notifies "File changed on disk — buffer reloaded." (fires only after nvim
  detected an external change and reloaded; `BufReadPost` would spam on every file open).

Events: alt-tab back (`FocusGained`), buffer switch, `CursorHold(I)` after `updatetime` ms (LazyVim: 200),
returning from `:terminal`. Guards: `nofile` skips scratch/UI buffers (Lazy, Mason, neo-tree, `:help`,
quickfix, telescope; no mtime); `getcmdwintype()` because `:checktime` errors inside `q:`.

### Control (opt-in)

The Nvim MCP server is installed but **not loaded by default**.

- `coder/claudecode.nvim` is installed in Nvim for selection push and Claude diff review, terminal
  provider `none`.
- `linw1995/nvim-mcp` and the `nvim-mcp` binary are installed; the MCP server is only injected by
  explicit launch commands. Its debug logs go to `/tmp/nvim-mcp.log`, not the project directory.
- `claude-nvim` launches Claude Code with `--strict-mcp-config --mcp-config ~/.claude/nvim-mcp.json --ide`.
- `codex-nvim` launches Codex with per-command `mcp_servers.nvim.*` overrides, starting from `mcp_servers={}`.
- Plain `claude` and `codex` get no Nvim MCP server. Use `claude-nvim` / `codex-nvim` when the agent
  should inspect Nvim state.

Managed files: `home/private_dot_config/nvim/lua/plugins/agent-integrations.lua`,
`home/dot_claude/nvim-mcp.json`, `home/dot_local/bin/executable_claude-nvim`,
`home/dot_local/bin/executable_codex-nvim`.

Default stack: **Option 2 + Option 1** below (`coder/claudecode.nvim`, terminal provider external, plus a
per-project `neovim` skill for RPC); each layer is independently reversible. Option 2 is non-negotiable for
the diff gate (otherwise Claude's edits land directly and step-by-step review collapses). Add Option 1 when
repeatedly typing "look at my cursor / diagnostics / this line".

### Control options compared

| Axis | Option 1 (skill) | Option 2 (plugin) | Option 3 (MCP server) |
|---|---|---|---|
| **Push**: user hands Claude a specific range | no | `ClaudeCodeSend` | no |
| **Pull**: Claude reads cursor / diagnostics / buffer itself | shell-composed | no | structured |
| **Steer**: Claude jumps to line, runs `:` cmd | yes | no | yes |
| **Diff gate**: review proposed edits before they land | no | yes | no |
| **Plugin-free** | yes | no (bridge plugin) | yes (separate server) |
| **Auto-discovery** | needs socket convention | lock file | manual config |

- **Option 1: RPC + skill.** Skill at `~/.claude/skills/neovim/SKILL.md` teaches
  `nvim --server <socket> --remote-expr '<vim expr>'` (read state), `--remote-send '<keys>'` (simulate
  keys), `--remote <file>` (open file). No selection push, no diff gate.
- **Option 2: `coder/claudecode.nvim`.** Pure-Lua, zero-dependency WebSocket server implementing the MCP
  protocol of Anthropic's VS Code / JetBrains extensions. Writes `~/.claude/ide/<port>.lock`; the `claude`
  CLI auto-detects it. Not an embedded AI (no chat buffer, no model calls from nvim). Gives diff gate,
  `:ClaudeCodeSend`, `@file` mentions. Ignore `:ClaudeCode` (opens `:terminal claude` inside nvim); set
  `terminal = { provider = "external" }` to keep Claude out of nvim.
- **Option 3: MCP server** (`bigcodegen/mcp-neovim-server`, `linw1995/nvim-mcp`). Standalone process
  speaking MCP to Claude and msgpack-RPC to nvim; tools `get_cursor_position`, `get_diagnostics`,
  `run_vim_command`, `replace` / `replaceAll` / `insert`. Better pull ergonomics than Option 1.

## How to

Socket discovery when Claude runs **inside** nvim's `:terminal`: `$NVIM` is set automatically (Averpil's pattern):

```bash
nvim --server "$NVIM" --remote-expr '<expr>' 2>/dev/null | grep -v '^Warning: Using NVIM_APPNAME='
```

(The `grep` strips an `NVIM_APPNAME` warning that otherwise corrupts stdout.)

In a **separate kitty pane** `$NVIM` is not set. Options:
- Use the `nvim-listen` shell function in `home/dot_zshrc`: it sets `NVIM_LISTEN_ADDRESS` to nvim-mcp's
  discoverable socket convention before launching `nvim` (the deployed opt-in convention).
- Or an nvim `VimEnter` autocmd writes `v:servername` to a cwd-derived path for the skill to read back.
- Or glob `$XDG_RUNTIME_DIR/nvim.*.0` (nvim's default location); works if only one nvim runs.

Kitty remote control lets hooks manage panes (complements the nvim RPC channel). In `kitty.conf`:
`allow_remote_control yes`, `listen_on unix:/tmp/mykitty`. Then `kitty @ launch --type=window
--cwd=current`, `kitty @ focus-window --match title:nvim`, `kitty @ send-text --match …`.

If `get_targets` says no targets, inspect the live sockets:

```bash
find "$XDG_RUNTIME_DIR" /tmp -maxdepth 1 \( -type s -o -type l \) -name 'nvim*' -print
```

## Gotchas

- `autoread` is passive permission (lets nvim silently reload a clean buffer). `:checktime` is the actual
  mtime check, run automatically only on a few events (notably around `:!` shell-outs); it does not poll
  and does not fire on `FocusGained` by default. Without config, Claude's disk edits never trigger it and
  the buffer stays stale.
- `linw1995/nvim-mcp` 0.7.2 discovers only sockets named
  `$XDG_RUNTIME_DIR/nvim-mcp.<escaped-git-root>.<suffix>.sock` (`/tmp` as fallback search dir).
  `<escaped-git-root>` is the absolute git root with `/` replaced by `%`, matching the plugin's
  `generate_pipe_path()`. `--connect auto` filters to the current project root; `get_targets` lists all
  matching `nvim-mcp.*.sock` sockets. A generic socket such as `/run/user/$UID/nvim-<project>.sock` works
  only when passed explicitly to `connect`; it never appears in `get_targets` or auto-connects.
- The nvim plugin also calls `serverstart()` on load. Its config reuses `vim.env.NVIM_LISTEN_ADDRESS` when
  `nvim-listen` set one; otherwise it creates a second `nvim-mcp.<escaped-root>.<pid>.sock` for the same
  Neovim and Claude sees duplicate active targets.
- If the only socket is a generic old wrapper path, the Neovim pane came from a stale shell or old
  wrapper. Run `source ~/.zshrc` or `exec zsh`, confirm `type nvim-listen` shows the `nvim-mcp.` path
  logic, restart Neovim with `nvim-listen` (the wrapper prints the selected socket; it must start with
  `nvim-mcp.`), then restart `claude-nvim`. For a running session, a symlink named with the nvim-mcp
  convention temporarily makes the old socket discoverable.
- Option 3: edits land in place (no diff gate), no user-curated push, configured globally in
  `.claude/settings.json` (no per-project auto-detection), typically picks the first socket when two nvims
  run, and is an extra process.

## Tried and rejected

- Option 3 alone: only right if Claude may edit without a review gate; otherwise redundant with Option 2's
  push/diff and duplicates Option 1's pull.
- Baking Option 1's features (`run_command` / `get_cursor` / `send_keys`) into Option 2: (1) protocol
  parity, since `coder/claudecode.nvim` tracks the MCP shape of VS Code / JetBrains, which don't expose
  these, so it would fork the protocol; (2) least privilege, since `--remote-expr` hands Claude the whole
  `vim.*` namespace (`vim.fn.system`, `:!`, `:qa!`, file writes anywhere), wrong for an always-on bridge
  while a skill is opt-in and visible; (3) Option 2 is "contributor submitting patches, you review",
  Option 1 is "pair watching your screen".
- Claude Code `PostToolUse` hook on `Edit|Write|MultiEdit` pushing
  `nvim --server $NVIM_SOCKET --remote-send '<C-\><C-N>:checktime<CR>'` (not deployed): would remove the
  ~200 ms `CursorHold` latency during continuous typing. Only worth adding if the pause-to-reload window
  is noticeable. The autocmd also catches non-Claude changes (git pull, formatter); the hook only Claude's.

## Upstream

- [`coder/claudecode.nvim`](https://github.com/coder/claudecode.nvim): bridge plugin (Option 2).
- [Averpil, Teaching Claude Code to run commands in Neovim](https://fredrikaverpil.github.io/blog/2026/03/07/teaching-claude-code-to-run-commands-in-neovim/): skill pattern using `$NVIM` + `--remote-expr` (Option 1 reference implementation).
- [`mhinz/neovim-remote`](https://github.com/mhinz/neovim-remote): `nvr` CLI wrapper over `--remote`.
- [`bigcodegen/mcp-neovim-server`](https://github.com/bigcodegen/mcp-neovim-server): MCP server exposing nvim (Option 3).
- [`linw1995/nvim-mcp`](https://github.com/linw1995/nvim-mcp): alternative MCP server with first-class diagnostics.
- [Vim Tips Wiki, check file changed externally](https://vim.fandom.com/wiki/Have_Vim_check_automatically_if_the_file_has_changed_externally): canonical autoread/checktime pattern.
- [Kitty remote control](https://sw.kovidgoyal.net/kitty/remote-control/): `allow_remote_control`, `listen_on`, `kitty @`.
