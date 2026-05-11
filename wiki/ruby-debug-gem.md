---
title: Ruby debug gem
tags: [ruby, rails, debugging, workflow]
created: 2026-05-06
updated: 2026-05-07
---

# Ruby debug gem

Use `debug`/`rdbg` for tracing Rails code, inspecting framework/application internals, and verifying agent-made changes by stepping through the exact path a test or request takes.

## `debugger` vs `bundle exec rdbg`

In many Rails projects, the fastest workflow is just:

```ruby
debugger
# or
binding.break
```

Then run the app normally:

```bash
bin/rails test test/path/to_test.rb
bin/rails server
```

If the project has the `debug` gem loaded in `development` or `test`, execution stops at that line and opens an `(rdbg)` prompt. This is the everyday path when the suspected location is known.

Use `bundle exec rdbg -c -- ...` when more control is needed:

- run the whole command under the debugger from process start
- stop during boot or before the app reaches a source breakpoint
- set breakpoints without editing code
- enable `record on` before the target code runs
- load init commands with `-e` or `-x`
- open an attachable debug port for terminal, VS Code, or Chrome frontends
- avoid global/project gem version mismatches by using the project's bundled `rdbg`

Practical rule: start with `debugger` in code for a known spot. Use `bundle exec rdbg` when debugging startup, unknown paths, record/replay setup, attach mode, or version/loading issues.

## Rails tests

```bash
bundle exec rdbg -c -- bin/rails test test/path/to_test.rb
bundle exec rdbg -c -- bundle exec rake test
```

Add `debugger` or `binding.break` at the suspected path. At the `(rdbg)` prompt:

- `n` / `next`: step over
- `s` / `step`: step into
- Enter on an empty line: repeat the previous command
- `fin` / `finish`: finish the current frame
- `u` / `until`: run until a later line, method, or frame end
- `bt`: backtrace
- `f <n>`, `up`, `down`: select stack frames
- `info`, `info locals`, `info ivars`: inspect current frame state
- `p expr`, `pp expr`, `eval expr`: evaluate Ruby in the selected frame
- `ls` / `outline`: list methods, constants, locals, and ivars
- `whereami`, `list`, `list -`: redisplay source around current execution

## Rails server

Console-first:

```bash
bundle exec rdbg -O -n -c -- bin/rails server -p 3000
rdbg -A
```

Environment variable attach mode:

```bash
RUBY_DEBUG_OPEN=true bin/rails server
rdbg -A
```

Use named sessions or fixed ports when multiple processes are running:

```bash
bundle exec rdbg -O --session-name web -n -c -- bin/rails server -p 3000
bundle exec rdbg -O --port 12345 -n -c -- bin/rails server -p 3000
rdbg -A 12345
```

Remote TCP debug traffic is not encrypted; keep it bound to localhost unless deliberately debugging a container/remote process.

## Record and replay

`debug` has recording support:

```text
(rdbg) record on
(rdbg) step back
(rdbg) step
(rdbg) step reset
(rdbg) record off
```

`step back` replays backward through the collected execution log. While replaying, `step` moves forward through that log again. This is useful for checking the last few states before a failing assertion or exception.

Caveat: record/replay is slow and memory-heavy. Prefer enabling it close to the suspected path, often from a breakpoint with `record on`, rather than for an entire Rails request or whole test suite.

## Inspecting code and API

Switch to IRB from inside `rdbg` when source/API inspection matters:

```text
(rdbg) irb
irb:rdbg> show_source SomeClass#method
irb:rdbg> show_doc ActiveRecord::Relation#where
irb:rdbg> ls object
irb:rdbg> whereami
```

For all sessions, set IRB as the debug console:

```bash
RUBY_DEBUG_IRB_CONSOLE=1 bundle exec rdbg -c -- bin/rails test
```

Or add this to `~/.rdbgrc` through chezmoi source:

```text
config set irb_console 1
```

## Claude sidecar command

This dotfiles repo adds a `claude` command to both rdbg and IRB with separate, independent implementations.

The sidecars are intentionally verification-first: they should ground answers in the live app, schema, model code, or runtime state and should not guess from memory when that evidence is available.

They also follow a probe-backed-claims rule: they should not state a substantive fact, diagnosis, or behavioral claim unless they also show how to verify the same thing from IRB/rdbg. If the claim is visible in the captured transcript/context, they cite that cue briefly. If it is not visible yet, they should phrase it as a hypothesis and provide the exact console/debugger probe that would confirm or falsify it.

### In rdbg

Managed via `~/.rdbgrc.rb` (chezmoi source: `home/dot_rdbgrc.rb`):

```text
(rdbg) claude
(rdbg) claude what should I inspect next?
(rdbg) claude why is result false here?
```

On each call it captures the current frame, selected frame index, nearby source lines, locals, a short backtrace, app/test/lib frames from the current stack, current breakpoints, and a recent rdbg transcript of command inputs plus debugger output/errors, then forwards that to `~/.local/bin/rdbg-agent-prompt`.

The transcript is an in-memory ring buffer for the current rdbg session. It is intentionally short and does not persist across runs.

**Conversation resuming:** the first `claude` call in a debug session starts a new Claude conversation. Every subsequent call within the same session resumes it (`--resume <session_id>`), so Claude accumulates context across turns.

**What gets sent:**

- *First call:* full system instructions (role, response format) + live debugger context + recent transcript + question
- *Resumed calls:* the probe-backed-claims invariant + fresh debugger context + recent transcript + question. The full role boilerplate is not repeated, since Claude already has it from turn 1

The debugger context is always current (you may have stepped since the last call), but the role boilerplate is sent only once.

### In IRB / Rails console

Managed via `~/.irbrc` (chezmoi source: `home/dot_irbrc`):

```ruby
claude("what should I inspect next?")
claude("why is this relation empty?", 12)   # second arg: how many recent statements to include
```

IRB records recent console statements and includes them as a transcript.
There is also a raw command form, so you can type `claude what should I inspect next?` without quotes.
Like the rdbg sidecar, the first call starts a Claude conversation and later calls resume it, sending only console statements recorded since the previous `claude` call.
The resumed-call prompt repeats the probe-backed-claims invariant so the constraint does not depend only on the first turn's system instructions.

### Helpers

| Script | Used by |
|--------|---------|
| `~/.local/bin/rdbg-agent-prompt` | rdbg `claude` command |
| `~/.local/bin/irb-agent-prompt` | IRB `claude(...)` function |

The two helpers are independent — separate system prompts, separate context capture, separate Claude invocations.

## Agent verification loop

1. Read the agent diff and identify the intended behavior path.
2. Put `debugger` at the boundary just before the changed behavior.
3. Run the narrowest Rails test under `rdbg`.
4. Use `next` to verify unchanged setup code and `step` into changed calls.
5. Use `info locals`, `pp object`, `ls object`, and `show_source` to verify actual runtime contracts, not assumptions from the diff.
6. Use `catch ErrorClass` or `catch ... path: /app\/models/` when the failure path is unknown.
7. Use `record on` only around the suspicious section, then `step back` from a bad state to inspect how it formed.

## Useful advanced commands

- `break Class#method`: stop at a method without editing source
- `break file.rb:123 if: expr`: conditional breakpoint
- `break ... pre: command`: run a command before stopping
- `break ... do: command`: run a command and continue
- `catch ErrorClass`: stop when an exception is raised
- `watch @ivar`: stop when an instance variable changes; slow
- `display expr`: print an expression every time execution stops
- `trace call /regexp/`: trace selected calls
- `trace exception`: trace raised exceptions
- `trace ... into: tmp/debug-trace.log`: send trace output to a file

## Sources

- Ruby `debug` README: <https://github.com/ruby/debug>
- RubyDoc `debug` 1.11.1 README: <https://www.rubydoc.info/gems/debug>
- Rails debugging guide: <https://guides.rubyonrails.org/debugging_rails_applications.html>
- IRB documentation: <https://ruby.github.io/irb/>
- RubyGuides debug gem guide: <https://rubyguides.dev/guides/ruby-debugging-with-debug-gem/>
- Rails rdbg + VS Code article: <https://railsnotes.xyz/blog/rails-debugger-rdbg-vscode>
- Rails server rdbg + Ruby LSP article: <https://gpaddis.github.io/2025/01/23/debugging-rails-server-with-rdbg-and-lsp.html>
- Stack Overflow record/replay example: <https://stackoverflow.com/questions/76304347/is-there-a-way-to-save-execution-of-ruby-code-to-debug-it-using-step-by-step-rep>
- Koichi Sasada RubyConf 2021 slides: <https://www.atdot.net/~ko1/activities/2021_rubyconf.pdf>
