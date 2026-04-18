# Session File Schemas

Two files track every autoresearch session. Both live in the working directory.

## `.autoresearch.md` — Human-Readable Session Document

This is a living document. Update it after every experiment.

### Metric Mode Template

```markdown
# Autoresearch Session

## Config
- **Objective**: [what we're optimizing]
- **Mode**: metric
- **Metric command**: `[shell command]`
- **Direction**: [minimize | maximize]
- **Scope**: `[files/directories]`
- **Validation**: [commands, comma-separated]
- **Max iterations**: [N | unlimited]

## Baseline
- Value: [number + unit] (experiment #0)

## Current Best
- Value: [number + unit] (experiment #N, [±%] vs baseline)

## Key Learnings
- [Insight about what works and why]
- [Insight about what doesn't work and why]

## Summary of Attempts
| # | Description | Metric | vs Best | Status |
|---|-------------|--------|---------|--------|
| 1 | [what was changed] | [value] | [±%] | ✓ improvement / ✗ regression / ⚠ invalid / ❌ error |
```

### Exploration Mode Template

```markdown
# Autoresearch Session

## Config
- **Objective**: [what we're exploring/improving]
- **Mode**: explore
- **Scope**: `[files/directories]`
- **Test scenarios**:
  1. "[concrete situation to evaluate against]"
  2. "[another situation]"
  3. "[another situation]"
- **Validation**: [commands, or "none"]
- **Max iterations**: [N | unlimited]

## Baseline
- Experiment #0: [description of starting state]

## Current Best
- Experiment #N: [description of what changed]
- Won [X/Y] scenarios vs baseline

## Key Learnings
- [Why approach X works — the reasoning, not just the fact]
- [Why approach Y doesn't work — what it gets wrong]
- [Emerging pattern about what makes a good version]

## Summary of Attempts
| # | Description | Result | Status |
|---|-------------|--------|--------|
| 1 | [what was changed] | Won X/Y | ✓ improvement / ✗ regression / ⚠ invalid / ❌ error |
```

## `.autoresearch.jsonl` — Machine-Readable Log

Append-only. One JSON object per line. Never modify previous lines.

### Common Fields (Both Modes)

```json
{
  "id": 0,
  "timestamp": "2026-03-26T10:00:00Z",
  "type": "baseline | improvement | regression | invalid | error",
  "description": "Human-readable description of what was attempted",
  "mode": "metric | explore",
  "files_changed": ["path/to/file1", "path/to/file2"],
  "commit": "abc1234 | null",
  "hypothesis": "What we expected and why"
}
```

### Metric Mode Additional Fields

```json
{
  "metric": 42.1,
  "baseline_metric": 45.2,
  "best_metric": 40.0,
  "delta_vs_baseline": "-6.9%",
  "delta_vs_best": "+5.3%"
}
```

### Exploration Mode Additional Fields

```json
{
  "scenarios": [
    {
      "name": "Scenario description",
      "winner": "new | old | tie",
      "reason": "Why this version won/lost for this scenario"
    }
  ],
  "verdict": "2/3 new",
  "learning": "Key insight from this experiment"
}
```

### Entry Type Definitions

- **baseline**: Experiment #0. The starting measurement or evaluation before any changes.
- **improvement**: New version is better than current best. Changes committed.
- **regression**: New version is worse than current best. Changes reverted.
- **invalid**: Changes broke validation (tests, lint, compilation). Changes reverted. Not counted as a real attempt — the idea wasn't properly testable.
- **error**: Something went wrong with the measurement or environment, not with the code changes. Changes reverted. Investigate if this repeats.

### Example: Metric Mode Session (test speed optimization)

```jsonl
{"id":0,"timestamp":"2026-03-26T10:00:00Z","type":"baseline","mode":"metric","description":"Baseline measurement","metric":12.3,"files_changed":[],"commit":null,"hypothesis":null}
{"id":1,"timestamp":"2026-03-26T10:03:00Z","type":"improvement","mode":"metric","description":"Replace database fixtures with in-memory SQLite","metric":10.8,"baseline_metric":12.3,"best_metric":12.3,"delta_vs_baseline":"-12.2%","delta_vs_best":"-12.2%","files_changed":["tests/conftest.py"],"commit":"abc1234","hypothesis":"In-memory DB avoids disk I/O during test setup"}
{"id":2,"timestamp":"2026-03-26T10:06:00Z","type":"regression","mode":"metric","description":"Parallelize with pytest-xdist","metric":11.1,"baseline_metric":12.3,"best_metric":10.8,"delta_vs_baseline":"-9.8%","delta_vs_best":"+2.8%","files_changed":["pytest.ini"],"commit":null,"hypothesis":"Parallel test execution should reduce wall-clock time"}
```

### Example: Exploration Mode Session (skill improvement)

```jsonl
{"id":0,"timestamp":"2026-03-26T10:00:00Z","type":"baseline","mode":"explore","description":"Current commit skill","files_changed":[],"commit":null,"hypothesis":null}
{"id":1,"timestamp":"2026-03-26T10:05:00Z","type":"improvement","mode":"explore","description":"Added why-over-what guidance with concrete examples","scenarios":[{"name":"Single file bug fix","winner":"new","reason":"Commit message explained the root cause, not just the change"},{"name":"Large refactor across 10 files","winner":"new","reason":"Grouped changes by intent rather than listing files"},{"name":"New feature with tests","winner":"tie","reason":"Both versions produced adequate messages"}],"verdict":"2/3 new","files_changed":["~/.claude/skills/commit/SKILL.md"],"commit":null,"hypothesis":"Explaining why over what produces more useful commit messages","learning":"Concrete before/after examples in the skill are more effective than abstract rules about style"}
```
