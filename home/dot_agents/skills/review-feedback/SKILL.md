---
name: review-feedback
description: "Turn code-review feedback into per-thread sketches before touching any code. Use whenever the user posts review comments in any form: pasted GitLab/GitHub threads ([UNRESOLVED]/[RESOLVED] blocks with diff context and @reviewer replies), a reviewer's chat message, a list of review notes, or threads fetched with glab. Use it even when they only say \"fix\", \"apply this\" or paste the feedback with no request. Sketches each thread's change, asks about ambiguous intent, flags comments that should become a project rule, and applies nothing until the user says go."
---

# Review feedback

Review comments are a conversation, not a task list. When pasted threads went straight into
implementation, the user had to stop the agent ("stop sketch only!!!!", "stop, let's discuss
first"). A wrong guess costs a rewrite the reviewer then re-reviews, so the default is: understand,
sketch, wait.

## 1. Read the feedback as threads

- Split it into threads: one location (file:line, or "general") plus its messages in order.
- `[RESOLVED]` threads are context only. Don't act on them unless asked.
- Separate the reviewer's asks from the user's own replies (their handle, e.g. `@felix.eschey.ext`).
  The user's replies show what they already agreed to or pushed back on. The reviewer's latest
  message is what's being asked now.
- The diff in a paste can be older than the branch, so locate the code in the current tree.
- When threads come from `glab`, only read them. Posting a reply or resolving a thread is a write
  that needs the user's OK on the exact text.

## 2. Read the code and the rules

Read every file the threads point at, plus the project's rules (`.claude/rules/`, `CLAUDE.md`) on
the topic. A comment often restates a rule the change broke, so that's the first thing to check.

## 3. Report per thread, then stop

For each unresolved thread, in paste order:

```
### <n>. <file:line> — <gist in a few words>
Ask: "<the reviewer's words, quoted>"
Reading: what they want, in one or two sentences. If two readings are plausible, give both,
         say which you'd pick and why.
Sketch: a diff block, not applied. The smallest change that satisfies the ask: no unrelated
        cleanup, no new abstraction "while we're here".
Ripple: tests, callers, specs or docs the change drags along, or "none".
Rule?: does this reveal a project convention missing from the rules? If yes, the line you'd add
       and the rule file it belongs in. Usually "no": skip general best practice the model
       already knows.
```

End with the open questions (numbered, each answerable in one line) and the order you'd apply the
threads in. Then stop. Nothing is written to the project yet.

## 4. When the user says go

- Apply only the threads they named, or all of them if they said so, one thread at a time, and run
  the project's checks for the touched files after each.
- If applying shows a sketch was wrong, stop and say so instead of improvising another design.
- Offer reply text per thread if it helps; posting it is the user's call.
