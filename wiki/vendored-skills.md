---
title: Vendored Skills
tags: [ai-agents, skills, provenance]
created: 2026-07-22
updated: 2026-07-22
---

# Vendored Skills

Skills copied into this repo from external sources, with their origin so they can be re-synced or checked upstream.

## triskweline/skills

Source: https://github.com/triskweline/skills (`skills/<name>/SKILL.md`)

A planning + autonomous-implementation skill set. Upstream defines 7 skills; the two below are vendored here:

- `agree-on-everything` — resolve every implementation decision with the user before any code is written (decision table with numbers/slugs, recommended options, explicit agreement).
- `implement-autonomously` — carry requirements to a tested, self-reviewed implementation. **Vendored copy is simplified**: the upstream version chains 5 more skills (`work-in-branch`, `find-verification-tools`, `full-verification`, `effective-rails-testing`, `self-review`) that we did not vendor, so those calls were stripped.

Not vendored (upstream only): `work-in-branch`, `find-verification-tools`, `full-verification`, `effective-rails-testing`, `self-review`.
