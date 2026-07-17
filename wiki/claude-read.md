---
title: claude-read
tags: [claude-code, output-styles, wrapper, neovim, nvim-mcp, read-only]
created: 2026-06-19
updated: 2026-06-19
---

# claude-read

A wrapper that runs Claude Code in **read mode** — cooperative, strictly read-only close reading of source code in your Neovim instance, in small verified steps. It fuses the discipline of [claude-solve](claude-solve.md) with the Nvim bridge of `claude-nvim` (see [Claude Code + Neovim](claude-code-neovim.md)), but oriented at *understanding* rather than building.

## What it does

`claude-read [<path>] [claude args...]`:

1. **Resolves the target and roots everything at its project/gem root.** The first non-flag arg is the target: a path *or* a gem name (resolved via `bundle show <name>` from the current project, so `claude-read actionpack` opens the gem's source). Both Nvim and Claude are rooted at the target's project root — the nearest ancestor with `.git`, a `*.gemspec`, or a `gems/` parent (`find_project_root`) — **not** the launcher's own cwd. This is what makes search / LSP / rubocop resolve within the thing you're reading instead of the outer worktree. The launcher `cd`s there before starting Claude.
2. **Opens the source in a Neovim split on a socket it chooses** — a new kitty window in the current tab (`kitty @ launch --type=window --cwd "$root"`) running `nvim --listen "$socket" "$abspath"`, where `$socket = $XDG_RUNTIME_DIR/nvim-mcp.<escaped-root>.read-<pid>.sock`. The launcher then **waits** (polls ~10s) for that socket to appear.
3. **Starts Claude with the bridge pointed explicitly at that socket** — a per-invocation MCP config (mktemp) with `--connect "$socket"` (**not** `auto`), so the nvim-mcp server connects to that exact path at startup:

   ```bash
   # generated mcp config
   { "mcpServers": { "nvim": { "command": "~/.cargo/bin/nvim-mcp",
       "args": ["--log-file","/tmp/nvim-mcp.log","--log-level","info","--connect","<socket>"] } } }

   claude --settings ~/.claude/read/settings.json \
          --strict-mcp-config --mcp-config <generated> --ide --name read "$@"
   ```

   It also exports `BUNDLER_EDITOR=~/.local/bin/nvim-open` and `CLAUDE_READ_NVIM_SOCKET=$socket` so `bundle open` and `nvim-open` target this same Nvim. `--strict-mcp-config` loads only the Nvim server; `--settings` scopes the output style to this invocation. If the bridge can't be brought up (not in kitty, no nvim-mcp, or socket never appears) it starts Claude **without** the bridge and prints the `nvim --listen <socket>` command — and the output style's startup gate then refuses to read until it's fixed.

### Why explicit `--connect`, not `auto`

`--connect auto` discovers sockets named `nvim-mcp.<escaped-git-root>.<pid>.sock` (created by the lazy `linw1995/nvim-mcp` **plugin**'s `serverstart`, see `init.lua:108`) and filters them to Claude's project root. In practice this failed: in a git **worktree** the roots didn't line up, and the lazy plugin often hadn't loaded at all, so no discoverable socket existed (nvim's default `nvim.<pid>.0` socket doesn't match). Verified via `/tmp/nvim-mcp.log`: *"No Neovim instances found for current project."* Pinning `--connect <socket>` to a path the launcher owns sidesteps discovery, the worktree-root filter, and the plugin entirely — confirmed by test (`INFO nvim_mcp: Connected to specific target … with ID …`). The MCP server talks to nvim's built-in RPC over the `--listen` socket, so the plugin isn't needed for reading/navigation.

## What it activates

`~/.claude/read/settings.json` sets **only** `outputStyle: "read"` — there are **no guard hooks**. The output style alone governs behavior (the user's call: "the output style should be enough for most things"). Unlike claude-solve, nothing hard-blocks tools, so legitimate read tooling like `bundle show`/`gem which` just works instead of being mistaken for "running project code."

The `read` output style (`~/.claude/output-styles/read.md`, `keep-coding-instructions: true`) is the close-reading discipline:

- **Confirm the bridge first (hard gate)** — before any reading, Claude makes one cheap Nvim tool call to prove the bridge is live. If it isn't, it **stops** and reports that setup must be fixed — it does *not* read source or fall back to citing `file:line`. (The user's requirement: don't start reading before the connection works.)
- **Read-only by intent** — Claude changes nothing (no edits, no notes file), but the shell is free for *looking*: search, inspect (`git diff`/`log`/`blame`), and resolve where library code lives (`bundle show <gem>`, `gem which`, …). It just shouldn't edit, run the app's mutating/side-effecting commands, or commit.
- **Accurate, simple, on point** — a sentence or two by default; depth only when the human asks ("explain"/"why"/"more").
- **Verify by looking** — every claim backed by something actually read (jump to definition, grep callers, read the test/`git blame`); cite evidence as `file:line`; never assert what code "probably" does.
- **One small step at a time**, the human sets direction, Socratic but terse.
- **You manage the navigation** — the human sets the goal; Claude opens the relevant file and jumps to the line/symbol in their Nvim each step (just does it), one place at a time. To read gem/library code, `bundle open <gem>` lands in their Nvim (see below), or it resolves the path (`bundle show <gem>`) and opens it via `nvim-open`/the bridge.
- **Re-root on request** — when the human points Claude at a different gem/project ("now read actionpack"), Claude resolves that root and `:cd`s the Nvim window there so search/LSP/rubocop re-scope to it. Allowed `:commands` are navigation/scope only (`:edit`/`:cd`/`:lcd`/`:tcd`/jumps); never edits, saves, mutating `:!`, or destructive commands.

## Forwarding `bundle open` (and other editor launches) into the Nvim split

`bundle open <gem>` runs `[$BUNDLER_EDITOR, $VISUAL, $EDITOR].first <gem-path>` (verified at `bundler/cli/open.rb:14` — note the var is **`BUNDLER_EDITOR`**, not `BUNDLE_EDITOR`). `claude-read` exports `BUNDLER_EDITOR=~/.local/bin/nvim-open`, so the gem opens in the *running* Nvim instead of a fresh editor.

`nvim-open` targets `$CLAUDE_READ_NVIM_SOCKET` (exported by `claude-read`) if set, else discovers the newest `nvim-mcp.<escaped-root>.*.sock` for the current git root, and runs `nvim --server <socket> --remote-tab-silent <file>`. Because it talks to nvim's `--listen` socket directly, it works **independently of the MCP bridge** and returns immediately (non-blocking). Also usable by hand: `nvim-open path/to/file`. Verified end-to-end (a forwarded file lands as a new buffer in the running instance). To forward *all* editor launches (`gem open`, git's editor, …) also export `VISUAL`/`EDITOR` — left to `BUNDLER_EDITOR` only by default to avoid surprising blocking-editor expectations elsewhere.

## How it differs from claude-solve

read mode is the **leaner sibling**. claude-solve's machinery — the `solve.md` scaffold, 20-line edit caps, the 4-file task-folder protocol, task scripts, scratch git repos, `reads.log`, and its `PreToolUse` guard hooks — exists for *building* (TDD, running experiments, checkpointing dirty changes). Read mode has **none** of that, not even guard hooks: it's governed by the output style alone. It adds one thing claude-solve lacks: it **launches Nvim in a split and connects to it** over MCP — on a socket it owns, with explicit `--connect`, so the bridge attaches reliably even in worktrees.

## chezmoi sources

| Source (`home/`) | Deployed |
|---|---|
| `dot_local/bin/executable_claude-read` | `~/.local/bin/claude-read` |
| `dot_local/bin/executable_nvim-open` | `~/.local/bin/nvim-open` |
| `dot_claude/output-styles/read.md` | `~/.claude/output-styles/read.md` |
| `dot_claude/read/settings.json` | `~/.claude/read/settings.json` |

Deploy after editing: `chezmoi -S home apply ~/.claude/output-styles ~/.claude/read ~/.local/bin/claude-read ~/.local/bin/nvim-open`.

## Notes / limits

- **No hard enforcement.** Read-only is an instruction in the output style, not a hook — Claude *can* technically edit or run anything; the style tells it not to. This was a deliberate trade (the earlier hard `bash-guard` kept blocking legitimate reads like `bundle show`).
- **The bridge is gated, not best-effort.** The output style forbids reading until the bridge is confirmed live, so a failed connection surfaces immediately instead of silently degrading to `file:line`.
- **Per-invocation MCP config leaks a tiny tempfile.** Because the launcher `exec`s into claude, the mktemp'd MCP config isn't cleaned up; it's a small JSON in `$TMPDIR`, cleared on reboot.
- **Plugin-dependent tools** (e.g. diagnostics streaming from `linw1995/nvim-mcp`) won't be available unless that lazy plugin is actually loaded in the split — core read/navigate over raw RPC is unaffected.
