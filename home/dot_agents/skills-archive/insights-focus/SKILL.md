---
name: insights-focus
description: Distill the latest Claude Code /insights report into a focused two-section digest — what's working well and what must change. Use when the user wants the punchy version of their usage insights, not the full report. Trigger on "what's working for me", "what should I change", "focused insights", "/insights-focus", or any request for a prioritized digest of recent Claude Code usage patterns.
---

# insights-focus

Produce a short, prioritized digest of the user's latest Claude Code usage insights. Two sections only — keep it tight.

## Inputs

The latest insights report lives at:
- `~/.claude/usage-data/report.html` — rendered report
- `~/.claude/usage-data/facets/*.json` — per-session structured data

Prefer reading `report.html` (fast, already synthesized). Fall back to the facets JSONs only if the HTML is missing or the user asks for fresher analysis than the last `/insights` run.

If neither exists, tell the user to run `/insights` first.

## Output format

Output exactly two sections, in this order:

### What's working

Bulleted list of 4–7 concrete patterns the user is doing well. Each bullet:
- Names the pattern in bold (e.g. **Planning-first rituals**)
- One or two sentences of evidence pulled from the report
- Tie to a specific session, count, or skill where possible

Keep it grounded in the report — no generic praise. If the report says a pattern is working, quote the evidence.

### What to change

Ruthlessly prioritized. Pick **one** highest-ROI change and lead with it as "The one thing". Then a short "Everything else is optional" paragraph listing lower-priority items the user could skip or defer.

Do not list every friction item. The user already has the full report for that. The job of this skill is to force a priority ranking.

## Style

- No headers beyond the two sections above.
- No emoji.
- No tables unless the user explicitly asks.
- Honest about limits — if something is "must change" vs "nice to have", say so.
- Total length: under 400 words for the whole output.

## What this skill is NOT

- Not a re-run of `/insights` — does not regenerate the report, only distills the existing one.
- Not a full friction audit — for that, the user reads the HTML report directly.
- Not a planning document — does not propose implementations. It names what to change; the user decides next steps.
