# Shared Interactive Skill Principles

These principles apply to all interactive (checkpoint-based) skills: scout, plan, review, walkthrough, diff-review, explore-solutions, autoresearch, control-flow-trace.
Card-based skills in project-local trees (e.g. study-card) also follow these principles.

## Information Density Rule

- Never present a wall of text with multiple assumptions, findings, or concepts at once.
- Each checkpoint may contain one or more **steps** when the material is too long to present at once. Use steps only when splitting genuinely helps — a checkpoint that fits in one message needs no steps.
- Each step covers ONE concept, ONE code path, or ONE question.
- After each step (or single-step checkpoint), pause for back-and-forth discussion before advancing.
- Keep each message short enough to take in without scrolling (code excerpts aside). Depth comes from multiple exchanges, not long monologues.
- The developer should never have to scroll back to process what was said.

## Progress Footer

> **Authoritative source is each SKILL.md.** Every interactive skill inlines its own "Output Contract — Progress Footer" section with a skill-specific denominator and example (e.g. scout uses `Checkpoint N/5`, plan uses `Checkpoint N/3`, walkthrough uses `Phase: <name> — <concept>`). Read the skill's own contract — do not rely on this file for the footer format.

Generic format (reference only):

- **With steps:** `Step 1/2 · Checkpoint 3/4 — <checkpoint title>: <step description>`
- **Without steps:** `Checkpoint 3/4 — <checkpoint title>`

The footer is a single line at the bottom of each message; its description is a short phrase, not a sentence.

## Respecting Developer Expertise

- If the developer says "I already know this," "skip," or demonstrates clear understanding, fast-forward.
- Do not lecture experienced developers on code they wrote or concepts they clearly grasp.
- If the developer requests the full output without checkpoints, produce the written artifact directly.

## Handling Disagreement

- When the developer pushes back on a finding or conclusion, re-evaluate the evidence rather than holding firm or immediately conceding.
- If the disagreement is about a design trade-off (not a factual error), mark it as "developer-accepted risk" and move on.
- Never dismiss developer expertise; never blindly agree either — show the evidence and let them decide.

## Scope Awareness

- If the input is very large (50+ files, 2000+ lines, broad epic), suggest narrowing scope or splitting into multiple sessions before proceeding.
- If the input is trivial (typo, single-line fix, formatting-only), offer a fast path that skips the full checkpoint ceremony.

## Message Length

- If one concept takes more than a few short paragraphs to explain, you are probably covering several — split into separate steps.
- Code excerpts can be longer but should be trimmed to the relevant lines with context.

## Code Snippet Format

When showing code in walkthroughs, traces, or evidence blocks, always use fenced code blocks with the file path and line range in the info string. Include the enclosing method, class header, or block so the excerpt is self-contained — never show isolated lines ripped from their surrounding context.

Format: ` ```<lang> <path>:<start>-<end> `

Example:

```ruby app/models/announcement.rb:3-14
class Announcement < ApplicationRecord
  scope :published, -> { where("publish_on < ?", Date.current) }
  scope :not_deleted, -> { where(deleted: false) }

  # ...

  def visible?
    published? && !deleted?
  end
end
```

- The file path and line range orient the developer — they can jump straight to the source.
- The surrounding block (class, method, or scope) provides enough context to understand the excerpt without reading the full file.
- Use `# ...` (comment-style for the language) to mark where lines were omitted. This signals that code exists between the shown sections but isn't relevant to the point being made.
- Trim to the smallest self-contained block that includes the relevant lines. Don't dump entire files.

## Non-Interactive Mode

When running as a subagent, in report-only mode, or when the developer explicitly requests no checkpoints:

- Produce the full output in a single pass. Do not pause for confirmation between checkpoints.
- Compress checkpoint structure into clearly labeled sections rather than eliminating it — the sections still organize the thinking.
- Omit interactive questions but preserve decision gates and open questions as labeled items in the output.
- If a tool is unavailable (e.g., Bash blocked, file write denied), note the limitation and continue with what's available. Never halt the entire skill because one tool failed.
- Prioritize the highest-risk areas when context budget is limited — read the most important files first, not all files equally.
