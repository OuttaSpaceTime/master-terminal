---
title: Ruby debug gem
tags: [ruby, rails, debugging, workflow]
created: 2026-05-06
updated: 2026-10-25
---

# Ruby debug gem

Use `debug`/`rdbg` for tracing Rails code, inspecting framework/application internals, and verifying
agent-made changes by stepping through the exact path a test or request takes.

## Current setup

This dotfiles repo adds a `claude` command to both rdbg and IRB, as two independent implementations
(separate system prompts, context capture and Claude invocations).

| Piece | Source | Live |
|---|---|---|
| rdbg `claude` command | `home/dot_rdbgrc.rb` | `~/.rdbgrc.rb` |
| IRB `claude(...)` function | `home/dot_irbrc` | `~/.irbrc` |
| rdbg helper | | `~/.local/bin/rdbg-agent-prompt` |
| IRB helper | | `~/.local/bin/irb-agent-prompt` |

Both sidecars are verification-first: ground answers in the live app, schema, model code or runtime state,
not memory. Probe-backed-claims rule: no substantive fact, diagnosis or behavioral claim without also showing
how to verify it from IRB/rdbg. If the claim is visible in the captured transcript, cite that cue briefly;
otherwise phrase it as a hypothesis with the exact console/debugger probe that would confirm or falsify it.

Both start a Claude conversation on the first `claude` call and resume it on later ones (rdbg:
`--resume <session_id>`), so context accumulates.

- rdbg: each call captures the current frame, selected frame index, nearby source, locals, a short
  backtrace, app/test/lib frames, breakpoints and a recent transcript of command inputs and debugger
  output/errors, then forwards it to `rdbg-agent-prompt`. The transcript is a short in-memory ring buffer
  per session, not persisted. First call sends full system instructions + context + transcript + question;
  resumed calls send the probe-backed-claims invariant + fresh context + transcript + question (role
  boilerplate only once).
- IRB: records recent console statements as the transcript. Resumed calls send only statements recorded
  since the previous `claude` call and repeat the probe-backed-claims invariant, so the constraint does not
  depend on turn 1.

Usage:

```text
(rdbg) claude why is result false here?
```

```ruby
claude("why is this relation empty?", 12)   # second arg: how many recent statements to include
```

IRB also accepts the raw form `claude what should I inspect next?` without quotes.

## How to

### `debugger` vs `bundle exec rdbg`

For a known spot, put `debugger` (or `binding.break`) in code and run normally (`bin/rails test
test/path/to_test.rb`, `bin/rails server`). With the `debug` gem loaded in `development` or `test`,
execution stops there at an `(rdbg)` prompt.

Use `bundle exec rdbg -c -- ...` for startup, unknown paths, record/replay setup, attach mode, or
version/loading issues. It can: run the whole command under the debugger from process start; stop during
boot; set breakpoints without editing code; `record on` before the target code runs; load init commands
with `-e` or `-x`; open an attachable port for terminal, VS Code or Chrome frontends; use the project's
bundled `rdbg` (avoids global/project gem version mismatches).

### Rails tests

```bash
bundle exec rdbg -c -- bin/rails test test/path/to_test.rb
bundle exec rdbg -c -- bundle exec rake test
```

At the `(rdbg)` prompt:

- `n`/`next` step over; `s`/`step` step into; Enter on an empty line repeats the previous command
- `fin`/`finish` finish the frame; `u`/`until` run until a later line, method or frame end
- `bt` backtrace; `f <n>`, `up`, `down` select frames
- `info`, `info locals`, `info ivars` inspect the frame; `p expr`, `pp expr`, `eval expr` evaluate in it
- `ls`/`outline` list methods, constants, locals, ivars; `whereami`, `list`, `list -` redisplay source

### Rails server

```bash
bundle exec rdbg -O -n -c -- bin/rails server -p 3000    # console-first, then: rdbg -A
RUBY_DEBUG_OPEN=true bin/rails server                    # env-var attach mode, then: rdbg -A
# named session / fixed port when several processes run
bundle exec rdbg -O --session-name web -n -c -- bin/rails server -p 3000
bundle exec rdbg -O --port 12345 -n -c -- bin/rails server -p 3000
rdbg -A 12345
```

### Record and replay

`record on`, `step back`, `step`, `step reset`, `record off` at the `(rdbg)` prompt. `step back` replays
backward through the collected log; `step` then moves forward through it again. Useful for the last few
states before a failing assertion or exception.

### Inspecting code and API

Switch to IRB from inside `rdbg`:

```text
(rdbg) irb
irb:rdbg> show_source SomeClass#method    # also: show_doc ActiveRecord::Relation#where, ls object, whereami
```

IRB as the debug console for all sessions: `RUBY_DEBUG_IRB_CONSOLE=1 bundle exec rdbg -c -- bin/rails test`,
or `config set irb_console 1` in `~/.rdbgrc` (through chezmoi source).

### Agent verification loop

1. Read the agent diff; identify the intended behavior path.
2. Put `debugger` just before the changed behavior; run the narrowest Rails test under `rdbg`.
3. `next` over unchanged setup, `step` into changed calls.
4. `info locals`, `pp object`, `ls object`, `show_source` verify actual runtime contracts, not assumptions from the diff.
5. `catch ErrorClass` or `catch ... path: /app\/models/` when the failure path is unknown.
6. `record on` only around the suspicious section, then `step back` from a bad state.

### Advanced commands

- `break Class#method`: stop at a method without editing source
- `break file.rb:123 if: expr`: conditional breakpoint
- `break ... pre: command`: run a command before stopping; `break ... do: command`: run it and continue
- `catch ErrorClass`: stop when an exception is raised
- `watch @ivar`: stop when an instance variable changes; slow; `display expr`: print on every stop
- `trace call /regexp/`, `trace exception`, `trace ... into: tmp/debug-trace.log`

## Gotchas

- Record/replay is slow and memory-heavy: enable it near the suspected path (often from a breakpoint with
  `record on`), not for a whole Rails request or test suite.
- Remote TCP debug traffic is not encrypted: keep it bound to localhost unless deliberately debugging a
  container/remote process.

## Upstream

- Ruby `debug` README: <https://github.com/ruby/debug>
- RubyDoc `debug` 1.11.1 README: <https://www.rubydoc.info/gems/debug>
- Rails debugging guide: <https://guides.rubyonrails.org/debugging_rails_applications.html>
- IRB documentation: <https://ruby.github.io/irb/>
- RubyGuides debug gem guide: <https://rubyguides.dev/guides/ruby-debugging-with-debug-gem/>
- Rails rdbg + VS Code article: <https://railsnotes.xyz/blog/rails-debugger-rdbg-vscode>
- Rails server rdbg + Ruby LSP article: <https://gpaddis.github.io/2025/01/23/debugging-rails-server-with-rdbg-and-lsp.html>
- Stack Overflow record/replay example: <https://stackoverflow.com/questions/76304347/is-there-a-way-to-save-execution-of-ruby-code-to-debug-it-using-step-by-step-rep>
- Koichi Sasada RubyConf 2021 slides: <https://www.atdot.net/~ko1/activities/2021_rubyconf.pdf>
