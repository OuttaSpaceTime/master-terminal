---
title: Claude Code + Neovim Integration
tags: [claude-code, neovim, lazyvim, integration]
created: 2026-04-21
updated: 2026-04-21
---

# Claude Code + Neovim Integration

Running Claude Code in a kitty pane next to nvim (LazyVim) produces two distinct problems with different solutions:

1. **Reload** — nvim does not pick up file changes Claude makes on disk.
2. **Control / forwarding** — Claude cannot see or steer nvim state.

Keep them separate. The reload fix is a local nvim concern. Control is an IPC concern over nvim's msgpack-RPC socket.

## Problem 1: Reload

### Mechanism

- `autoread` is **passive permission** — it allows nvim to silently reload a clean buffer when a change is detected. It does not itself check anything.
- `:checktime` is the **actual mtime check**. Nvim runs it automatically only on a small set of events (notably around `:!` shell-outs). It does **not** poll on a timer, does not fire on `FocusGained` by default.

Net effect without config: Claude edits a file on disk, nothing triggers `:checktime`, buffer stays stale.

### Fix (deployed)

Autocmd group `auto_checktime` in `home/private_dot_config/nvim/lua/config/autocmds.lua`:

```lua
vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold", "CursorHoldI", "TermLeave" }, {
  group = checktime_group,
  pattern = "*",
  callback = function()
    if vim.fn.getcmdwintype() == "" and vim.bo.buftype ~= "nofile" then
      pcall(vim.cmd, "checktime")
    end
  end,
})

vim.api.nvim_create_autocmd("FileChangedShellPost", {
  group = checktime_group,
  pattern = "*",
  callback = function()
    vim.notify("File changed on disk — buffer reloaded.", vim.log.levels.INFO)
  end,
})
```

### Why the events

- `FocusGained` — alt-tab back into nvim.
- `BufEnter` — switching buffers.
- `CursorHold` / `CursorHoldI` — fires after `updatetime` ms of no keys (LazyVim sets 200 ms, so effectively instant during editing pauses).
- `TermLeave` — returning from `:terminal`.
- `FileChangedShellPost` — fires *only after* nvim has detected an external change and reloaded the buffer. Right hook for the user-visible "reloaded" notification; `BufReadPost` would spam on every file open.

### Why the guards

- `buftype ~= "nofile"` — skip scratch/UI buffers (Lazy, Mason, neo-tree, `:help`, quickfix, telescope). They have no mtime.
- `getcmdwintype() == ""` — `:checktime` errors inside the command-line window (`q:`).

### Belt-and-suspenders option (not deployed)

A Claude Code `PostToolUse` hook on `Edit|Write|MultiEdit` could push `:checktime` to nvim immediately via `nvim --server $NVIM_SOCKET --remote-send '<C-\><C-N>:checktime<CR>'`, eliminating the ~200 ms `CursorHold` latency during continuous typing. Only worth adding if the pause-to-reload window is noticeable in practice. Autocmd already catches non-Claude changes (git pull, formatter, etc.), hook catches only Claude's — they are complementary but not both required.

## Problem 2: Control / forwarding

Three tiers, chosen by how much Claude should see of nvim and how edits should be gated.

### Framing: push vs. pull, gate vs. direct

| Axis | Option 1 (skill) | Option 2 (plugin) | Option 3 (MCP server) |
|---|---|---|---|
| **Push**: user hands Claude a specific range | ❌ | ✅ `ClaudeCodeSend` | ❌ |
| **Pull**: Claude reads cursor / diagnostics / buffer on its own | ✅ shell-composed | ❌ | ✅ structured |
| **Steer**: Claude moves the user (jump to line, run `:` cmd) | ✅ | ❌ | ✅ |
| **Diff gate**: review proposed edits before they land | ❌ | ✅ | ❌ |
| **Plugin-free** | ✅ | ❌ (bridge plugin) | ✅ (separate server) |
| **Auto-discovery** | needs socket convention | ✅ lock file | manual config |

### Option 1 — Plain RPC + Claude Code skill

- Skill at `~/.claude/skills/neovim/SKILL.md` teaches Claude to use:
  - `nvim --server <socket> --remote-expr '<vim expr>'` — read state
  - `nvim --server <socket> --remote-send '<keys>'` — simulate keys
  - `nvim --server <socket> --remote <file>` — open file
- Socket discovery: `$NVIM` when Claude runs inside nvim's `:terminal`; otherwise needs a convention (e.g. write `v:servername` to a cwd-derived path on `VimEnter`).
- Unlocks: ambient pull, editor steering, structured diagnostics via Lua.
- Does not provide: selection-push or diff-review gate.

### Option 2 — Bridge plugin: `coder/claudecode.nvim`

- Pure-Lua, zero-dependency WebSocket server implementing the same MCP protocol Anthropic's VS Code / JetBrains extensions use.
- Writes `~/.claude/ide/<port>.lock`; the `claude` CLI auto-detects and connects.
- **Not an embedded AI.** No chat buffer, no model calls from nvim. Claude still runs in a separate kitty pane.
- Unlocks: diff-review gate, `:ClaudeCodeSend` for user-curated selection push, `@file` mentions.
- Ignore the `:ClaudeCode` command — it's an optional wrapper that opens `:terminal claude` inside nvim. Set `terminal = { provider = "external" }` in config to keep Claude out of nvim entirely.

### Option 3 — MCP server exposing nvim (`bigcodegen/mcp-neovim-server`, `linw1995/nvim-mcp`)

- Standalone process speaks MCP to Claude and msgpack-RPC to nvim.
- Structured tools: `get_cursor_position`, `get_diagnostics`, `run_vim_command`, `replace` / `replaceAll` / `insert` edits.
- Unlocks: ambient pull with **better ergonomics than Option 1** (structured tools → Claude pulls more readily).
- Missing vs. Option 2:
  - **No diff-review gate** — edits land in place.
  - **No user-curated push** — Claude pulls selection, user doesn't push it.
  - **No per-project auto-detection** — configured globally in `.claude/settings.json`, not contextual.
  - **Multi-nvim confusion** — typically picks first socket; ambiguous if two nvim instances are running.
  - **Extra process** to operate.

### Why Option 1's features aren't baked into Option 2

Not an oversight:

1. **Protocol parity.** `coder/claudecode.nvim` tracks Anthropic's MCP shape used by VS Code / JetBrains. Those don't expose `run_command` / `get_cursor` / `send_keys` either. Adding them would fork the protocol.
2. **Least privilege.** `--remote-expr` hands Claude the full `vim.*` namespace: `vim.fn.system`, `:!`, `:qa!`, file writes anywhere. An always-on bridge is the wrong place for that. A skill is opt-in and visible.
3. **Different paradigms.** Option 2 = "contributor submitting patches, you review." Option 1 = "pair watching your screen." VS Code protocol encodes the former.

The skill layer exists precisely to cover the pair-partner gap without forcing the plugin to grow a kitchen sink.

## Recommendation

For interactive pair-programming ("sparring partner" — Claude sees edits, suggests next step, jumps the cursor):

1. **Option 2 is non-negotiable** for the diff-review gate. Without it, Claude's edits land directly and slow step-by-step review collapses.
2. **Option 1 (skill) adds ambient pull and steering.** Worth it when you notice yourself repeatedly typing "look at my cursor / diagnostics / this line." Start without it; add if friction surfaces.
3. **Option 3 alone** is only right if you accept Claude editing without a review gate. Otherwise it's redundant with Option 2's push/diff and duplicates Option 1's pull.

Default stack: **Option 2 + Option 1**. Install `coder/claudecode.nvim` with terminal provider set to external; add a per-project `neovim` skill for RPC. Each layer is independently reversible.

## Socket discovery conventions

When Claude runs **inside** nvim's `:terminal`: `$NVIM` is set automatically by nvim. Averpil's pattern:

```bash
nvim --server "$NVIM" --remote-expr '<expr>' 2>/dev/null | grep -v '^Warning: Using NVIM_APPNAME='
```

(The `grep` strips an `NVIM_APPNAME` warning that otherwise corrupts stdout.)

When Claude runs in a **separate kitty pane**: `$NVIM` is not set. Options:

- Set `NVIM_LISTEN_ADDRESS=/run/user/$UID/nvim-$(basename "$PWD").sock` via a shell wrapper around `nvim`.
- Or: nvim `VimEnter` autocmd writes `v:servername` to a cwd-derived path for the skill to read back.
- Or: glob `$XDG_RUNTIME_DIR/nvim.*.0` (nvim's default socket location) — works if only one nvim is running.

No convention is deployed yet. Decide when setting up Option 1.

## Kitty-layer bonus

Orthogonal to the above, kitty remote control lets hooks manage panes:

```
# kitty.conf
allow_remote_control yes
listen_on unix:/tmp/mykitty
```

Then `kitty @ launch --type=window --cwd=current`, `kitty @ focus-window --match title:nvim`, `kitty @ send-text --match …`. Useful if a Claude hook should open a new pane or focus the nvim pane after an edit. Complements the nvim RPC channel; doesn't replace it.

## References

- [`coder/claudecode.nvim`](https://github.com/coder/claudecode.nvim) — bridge plugin (Option 2).
- [Averpil — Teaching Claude Code to run commands in Neovim](https://fredrikaverpil.github.io/blog/2026/03/07/teaching-claude-code-to-run-commands-in-neovim/) — skill pattern using `$NVIM` + `--remote-expr` (Option 1 reference implementation).
- [`mhinz/neovim-remote`](https://github.com/mhinz/neovim-remote) — `nvr` CLI wrapper over `--remote`.
- [`bigcodegen/mcp-neovim-server`](https://github.com/bigcodegen/mcp-neovim-server) — MCP server exposing nvim (Option 3).
- [`linw1995/nvim-mcp`](https://github.com/linw1995/nvim-mcp) — alternative MCP server with first-class diagnostics.
- [Vim Tips Wiki — check file changed externally](https://vim.fandom.com/wiki/Have_Vim_check_automatically_if_the_file_has_changed_externally) — canonical autoread/checktime pattern.
- [Kitty remote control](https://sw.kovidgoyal.net/kitty/remote-control/) — `allow_remote_control`, `listen_on`, `kitty @`.
