# HTML Overview Template

Used by `/diff-review` Checkpoint 1. The skill substitutes the `{{...}}` placeholders and
writes the result to `.claude/docs/diff-overviews/NNN-<branch>-YYYYMMDD.html`, then opens
it via `scripts/render_overview.sh <path> --open`.

## Placeholders

| Placeholder | Type | Notes |
|---|---|---|
| `{{TITLE}}` | text | e.g. `Diff Overview — add-theme-preference` |
| `{{META}}` | HTML | one `<span>` per fact; the CSS auto-inserts `·` separators. e.g. `<span>8 files</span><span>+187 / −12</span><span>branch add-theme-preference</span><span>2026-04-20</span>` |
| `{{TLDR}}` | inline HTML | one or two sentences naming what the change *does*, not the diff |
| `{{FILE_ROWS}}` | HTML `<tr>...</tr>` rows | one per changed file; emit empty string if there are zero (impossible in practice) |
| `{{RIPPLE_SECTION}}` | HTML block or empty string | the whole `<h2>Touches but does not modify</h2><ul>...</ul>` block, OR an empty string when no ripple files |
| `{{FLOW_SECTION}}` | HTML block or empty string | the whole `<h2>Execution flow</h2><pre class="mermaid">...</pre>` block (with the embedded `<script type="module">` once per page), OR an empty string when the diagram is gated off |
| `{{SIZE_INFO}}` | text | e.g. `+187 / −12 across 8 files` |
| `{{NUDGE_OR_EMPTY}}` | HTML block or empty string | `<div class="nudge">...</div>` only when total LOC > 400 (SmartBear ceiling) |

## File-row format

```html
<tr><td><span class="bucket b-feature"></span>Feature</td><td class="file-cell"><code>features/settings/settings.component.ts</code></td><td>adds <code>themeControl</code>; wires submit</td></tr>
```

The `b-<bucket>` class names come from `references/intent-buckets.md`.

## Ripple section format (when present)

```html
<h2>Touches but does not modify</h2>
<ul class="ripple">
  <li><code>core/interceptors/auth.interceptor.ts</code> — new PUT flows through; attach logic unchanged</li>
  <li><code>theme/theme.service.ts</code> — consumes <code>ThemeMode</code> from resolver; contract-compatible</li>
</ul>
```

## Flow section format (when present)

```html
<h2>Execution flow</h2>
<pre class="mermaid">
flowchart LR
  subgraph Save
    U[User submits form] --> C[SettingsComponent.save]
    C --> S[UserSettingsService.setTheme]
    S -->|PUT /api/settings| A[AuthInterceptor]
    A --> API[(Backend)]
  end
  subgraph Apply
    R[App bootstrap] --> RV[ThemeResolver]
    RV --> G[UserSettingsService.get]
    G --> TS[ThemeService.apply]
  end
  classDef new fill:#d4f4dd,stroke:#2d7a3a,color:#000
  classDef same fill:#f0f0f0,stroke:#999,stroke-dasharray:3 3,color:#000
  class C,S,RV new
  class A,TS same
</pre>
<noscript><div class="cdn-warn">Diagram requires the Mermaid script from <code>cdn.jsdelivr.net</code>. If your environment blocks it, re-run <code>/diff-review --offline</code> to embed a pre-rendered SVG instead.</div></noscript>
```

The `<script type="module">` tag at the bottom of `<body>` (see template below) imports
Mermaid once per page and starts it.

## Gating rule for the flow section

Render the flow section only when **either** of these holds:

- The diff touches files in 2+ distinct layers (component / service / resolver / interceptor / controller / middleware / util / types — judged from path conventions).
- The diff introduces a new public/exported symbol in a non-test file (heuristic: a `+export ` line in any non-`*.spec.*` / non-`*.test.*` file).

Otherwise emit empty string for `{{FLOW_SECTION}}`.

## Offline fallback

When `/diff-review --offline` (or detected CDN block during a future re-render): instead
of the `<pre class="mermaid">` block, write the same flow as a `.d2` file under
`/tmp/diff-overview-flow.d2`, invoke the `/d2` skill's `scripts/render_and_open.sh` to
produce an SVG, then inline the SVG markup directly into `{{FLOW_SECTION}}`. Drop the
`<noscript>` warning and the module-import script in this branch.

## Full template

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>
  :root { color-scheme: light dark; }
  body {
    font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    max-width: 760px; margin: 2rem auto; padding: 0 1rem;
    color: #1a1a1a; background: #fafafa;
  }
  @media (prefers-color-scheme: dark) {
    body { color: #e0e0e0; background: #181818; }
    th { background: #2a2a2a; }
    .tldr { background: #222; }
    th, td { border-color: #333; }
    code { background: #2a2a2a; }
  }
  header { margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #e4e4e4; }
  @media (prefers-color-scheme: dark) { header { border-bottom-color: #2a2a2a; } }
  h1 { font-size: 1.5rem; margin: 0 0 0.35rem; letter-spacing: -0.01em; }
  .meta { color: #888; font-size: 0.88rem; display: flex; flex-wrap: wrap; gap: 0.25rem 0.75rem; }
  .meta span { white-space: nowrap; }
  .meta span + span::before { content: "·"; margin-right: 0.75rem; color: #bbb; }
  .tldr { padding: 0.85rem 1.05rem; background: #fff; border-left: 3px solid #4a7ec1; margin: 1.25rem 0; border-radius: 0 4px 4px 0; }
  h2 { font-size: 1.05rem; margin-top: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 0.3rem; }
  table { border-collapse: collapse; width: 100%; font-size: 0.92rem; table-layout: fixed; }
  col.c-bucket  { width: 8.5rem; }
  col.c-file    { width: 22rem; }
  col.c-purpose { width: auto; }
  th, td { border: 1px solid #ddd; padding: 0.45rem 0.65rem; text-align: left; vertical-align: top; }
  th { background: #f0f0f0; }
  td.file-cell code { display: inline-block; max-width: 100%; white-space: normal; word-break: break-all; overflow-wrap: anywhere; line-height: 1.35; }
  code, pre { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 0.88rem; }
  code { background: #efefef; padding: 1px 4px; border-radius: 3px; }
  ul.ripple { padding-left: 1.2rem; }
  ul.ripple li { margin: 0.3rem 0; }
  .bucket { display: inline-block; width: 0.7em; height: 0.7em; border-radius: 50%; margin-right: 0.4em; vertical-align: baseline; }
  .b-feature  { background: #2d7a3a; }
  .b-fix      { background: #c0392b; }
  .b-refactor { background: #8e44ad; }
  .b-test     { background: #16a085; }
  .b-docs     { background: #2980b9; }
  .b-config   { background: #d68910; }
  .b-types    { background: #5d6d7e; }
  .b-other    { background: #95a5a6; }
  .size { color: #888; font-size: 0.9rem; margin-top: 1.5rem; }
  .nudge { background: #fff4d6; color: #7a5500; padding: 0.6rem 0.9rem; border-left: 3px solid #d68910; margin-top: 0.5rem; }
  .cdn-warn { background: #fff4d6; color: #7a5500; padding: 0.6rem 0.9rem; border-left: 3px solid #d68910; margin-top: 0.5rem; }
  pre.mermaid {
    text-align: center; background: transparent;
    width: min(1400px, calc(100vw - 2rem));
    margin-left: 50%; transform: translateX(-50%);
  }
  pre.mermaid svg { width: 100% !important; max-width: none !important; height: auto !important; }
</style>
</head>
<body>
<header>
  <h1>{{TITLE}}</h1>
  <div class="meta">{{META}}</div>
</header>

<div class="tldr"><strong>TL;DR.</strong> {{TLDR}}</div>

<h2>Changes by intent</h2>
<table>
  <colgroup>
    <col class="c-bucket">
    <col class="c-file">
    <col class="c-purpose">
  </colgroup>
  <thead><tr><th>Bucket</th><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
{{FILE_ROWS}}
  </tbody>
</table>

{{RIPPLE_SECTION}}

{{FLOW_SECTION}}

<div class="size">{{SIZE_INFO}}</div>
{{NUDGE_OR_EMPTY}}

<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
  mermaid.initialize({
    startOnLoad: true,
    theme: "default",
    securityLevel: "loose",
    flowchart: { useMaxWidth: false, htmlLabels: true, nodeSpacing: 50, rankSpacing: 60 }
  });
</script>
</body>
</html>
```

The `<script>` is harmless when no `<pre class="mermaid">` is in the DOM — Mermaid finds
nothing to render and exits silently. So the same template is used regardless of whether
the flow section is present.
