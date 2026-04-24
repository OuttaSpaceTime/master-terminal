# HTML Overview Template

Used by `/diff-review` Checkpoint 1. The skill writes one HTML page to
`.claude/docs/diff-overviews/NNN-<branch>-YYYYMMDD.html` and opens it via
`scripts/render_overview.sh <path> --open`.

## Page goal

This is the developer's 15-second orientation page. It should answer:

- What changed overall?
- Which folders/subtrees moved?
- Which untouched readers/consumers should still be in mind?
- If there is a cross-layer path, what did it look like before vs after the diff?

When a flow exists, the page should use tabs:

- `Overview` — path-true tree, indirect consumers section, compact flow summary
- `Control flow` — larger before/after Mermaid comparison

When no flow exists, render only the `Overview` tab content and omit the tab switcher.

## Placeholders

| Placeholder | Type | Notes |
|---|---|---|
| `{{TITLE}}` | text | e.g. `Diff Overview — add-theme-preference` |
| `{{META}}` | HTML | one `<span>` per fact; the CSS auto-inserts `·` separators |
| `{{TLDR}}` | inline HTML | one or two sentences naming what the change *does*, not the diff |
| `{{TABS_NAV_OR_EMPTY}}` | HTML block or empty string | the whole tab bar when control-flow exists |
| `{{OVERVIEW_PANEL_CLASS}}` | text | `tab-panel is-active` when tabs exist, otherwise `overview-only` |
| `{{TREE_SECTION}}` | HTML block | the whole path-true tree section |
| `{{INDIRECT_CONSUMERS_SECTION_OR_EMPTY}}` | HTML block or empty string | separate section for untouched downstream readers/consumers |
| `{{FLOW_SUMMARY_SECTION_OR_EMPTY}}` | HTML block or empty string | compact summary on the overview tab |
| `{{SIZE_INFO}}` | text | e.g. `+187 / −12 across 8 files` |
| `{{NUDGE_OR_EMPTY}}` | HTML block or empty string | `<div class="nudge">...</div>` only when total LOC > 400 |
| `{{FLOW_PANEL_OR_EMPTY}}` | HTML block or empty string | the whole `Control flow` panel, including before/after prose and diagrams |
| `{{SCRIPT_BLOCK_OR_EMPTY}}` | HTML block or empty string | the tab-switch + lazy Mermaid renderer script, only when flow exists |

## Tree section rules

- Use real path-oriented nesting. Favor 2-3 levels of hierarchy; stop when deeper nesting
  no longer improves orientation.
- Each group rolls up file count, Lines±, and a one-sentence behavioral summary.
- File leaves use a two-line rhythm: filename/stats on line 1, behavior note on line 2.
- Keep the main tree strictly path-true. Do not invent synthetic folders for ripple files.
- Put untouched downstream readers/consumers in a separate `Indirect consumers` section
  below the tree.
- Use the dominant bucket for a group badge. If the subtree is genuinely mixed, use `Mixed`.
- For binary files, render a file leaf note like `[binary, skipped]` and keep the file in totals.

## Tree section example

```html
<h2>Changes by tree</h2>
<p class="section-copy">Grouped into collapsible path levels. Each level rolls up file count, line delta, and a short behavioral summary.</p>

<div class="tree">
  <details open>
    <summary>
      <div class="summary-row">
        <div class="summary-main">
          <div class="summary-title">app/</div>
          <div class="summary-sub">2 files · +41 / −4 · Production-side fixes snapshot mutable data before inbox rendering.</div>
        </div>
        <div class="summary-stats">+41 / −4</div>
        <div class="summary-bucket bucket-fix">Fix</div>
      </div>
    </summary>
    <div class="details-body">
      <p class="path-line">Top-level effect: inbox message generation no longer depends on current associated records when historical payload is what the user needs to see.</p>
      <!-- nested groups / file leaves -->
    </div>
  </details>

</div>
```

## Indirect consumers section example

This section is curated, not exhaustive. It shows important untouched consumers of changed
output. The complete propagation story belongs in `Control flow`.

```html
<h2>Indirect consumers</h2>
<div class="indirect">
  <p class="indirect-copy">These files are not modified in the diff, but they sit on the read path of the changed content. They are listed separately so the main tree stays path-true.</p>
  <div class="indirect-list">
    <div class="indirect-item">
      <div class="indirect-head">
        <span class="indirect-label">Indirect</span>
        <span class="leaf-path">app/serializers/inbox/item_serializer.rb</span>
        <span class="muted">+0 / −0</span>
      </div>
      <span class="leaf-note">Still reads <code>title</code>/<code>body</code>; output changes only because upstream wording changed.</span>
    </div>
    <div class="indirect-item">
      <div class="indirect-head">
        <span class="indirect-label">Indirect</span>
        <span class="leaf-path">app/models/component_request/changed_item.rb</span>
        <span class="muted">+0 / −0</span>
      </div>
      <span class="leaf-note">Still consumes the same snapshot fields; now benefits from the corrected source values.</span>
    </div>
  </div>
</div>
```

## Flow summary section example

This lives in the `Overview` tab only when flow is gated on.

```html
<h2>Control flow summary</h2>
<div class="flow-summary">
  <p class="flow-summary-copy">The diff touches two user-facing inbox paths. The important part is that both now render from snapshotted event/request data instead of mutable associations.</p>
  <ul class="flow-points">
    <li><strong>CR path:</strong> <code>ComponentRequestPullJob</code> persists corrected snapshot fields before the serializer reads them.</li>
    <li><strong>Monitoring-list path:</strong> <code>BasicDataUpdatedItem</code> now uses <code>event.new_name</code>, which survives destroyed associations.</li>
    <li><strong>Why the graph matters:</strong> both flows converge at the same inbox boundary, but they fix different upstream failure modes.</li>
  </ul>
</div>
```

## Control flow panel example

Render two separate Mermaid graphs: `Before` and `After`.

```html
<section class="tab-panel" id="panel-flow" role="tabpanel" aria-labelledby="tab-flow">
  <h2>Control flow</h2>
  <p class="section-copy">This tab reserves the canvas for the execution map, so the first tab can stay focused on tree orientation and indirect-consumer summaries.</p>

  <div class="flow-shell">
    <div class="flow-stage">
      <div class="flow-card">
        <h3>Before this change</h3>
        <p>Inbox rendering followed live associations. That let historical messages drift with mutable state and could fail when associations disappeared.</p>
      </div>
      <div class="flow-card">
        <h3>After this change</h3>
        <p>Both message paths render from persisted snapshot data. The shared inbox boundary remains the same, but its inputs are now stable.</p>
      </div>
    </div>

    <div class="diagram-frame">
      <p class="diagram-label">Before: live associations leak into historical inbox rendering</p>
      <pre class="mermaid">
flowchart LR
  A[ChangedItem] -->|reads current association| I[Inbox::Item]
  C[(Current state)] -. mutable .-> I
  I --> S[Inbox::ItemSerializer]
      </pre>
    </div>

    <div class="diagram-frame" style="margin-top: 1rem;">
      <p class="diagram-label">After: snapshot data feeds the same inbox boundary</p>
      <pre class="mermaid">
flowchart LR
  A2[ChangedItem with snapshot data] --> I2[Inbox::Item]
  I2 --> S2[Inbox::ItemSerializer]
      </pre>
    </div>
  </div>
</section>
```

## Gating rule for the control-flow tab

Render the `Control flow` tab only when **either** of these holds:

- The diff touches files in 2+ distinct layers (component / service / resolver /
  interceptor / controller / middleware / util / types — judged from path conventions).
- The diff introduces a new public/exported symbol in a non-test file (heuristic: a
  `+export ` line in any non-`*.spec.*` / non-`*.test.*` file).

Otherwise omit `{{TABS_NAV_OR_EMPTY}}`, `{{FLOW_SUMMARY_SECTION_OR_EMPTY}}`,
`{{FLOW_PANEL_OR_EMPTY}}`, and `{{SCRIPT_BLOCK_OR_EMPTY}}`.

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
  * { box-sizing: border-box; }
  body {
    font: 16px/1.58 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    max-width: 1100px; margin: 2rem auto; padding: 0 1rem 3rem;
    color: #1a1a1a; background: #fafafa;
  }
  @media (prefers-color-scheme: dark) {
    body { color: #e0e0e0; background: #181818; }
    .tldr, .tabs-shell, .tree, .indirect, .flow-summary, .size-card, .flow-shell { background: #222; }
    details summary:hover, .tab:hover { background: rgba(255,255,255,0.04); }
    code { background: #2a2a2a; }
    .path-line, .leaf-note, .muted, .size, .section-copy, .summary-sub, .group-note, .flow-summary-copy, .indirect-copy { color: #aaa; }
    h2, header, .tabs-nav { border-bottom-color: #2a2a2a; }
    .details-body { border-left-color: #333; }
    .tab[aria-selected="true"] { background: #2a2a2a; color: #fff; }
    .indirect-item { border-color: #333; background: #202226; }
  }
  header { margin-bottom: 1.25rem; padding-bottom: 1rem; border-bottom: 1px solid #e4e4e4; }
  h1 { font-size: 1.5rem; margin: 0 0 0.35rem; letter-spacing: -0.01em; }
  h2 { font-size: 1.05rem; margin-top: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 0.3rem; }
  .meta { color: #888; font-size: 0.88rem; display: flex; flex-wrap: wrap; gap: 0.25rem 0.75rem; }
  .meta span { white-space: nowrap; }
  .meta span + span::before { content: "·"; margin-right: 0.75rem; color: #bbb; }
  .tldr, .tabs-shell, .tree, .indirect, .flow-summary, .size-card, .flow-shell {
    background: #fff; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }
  .tldr {
    padding: 0.9rem 1.1rem; border-left: 3px solid #4a7ec1; margin: 1.25rem 0 1rem;
    border-radius: 0 12px 12px 0;
  }
  .tabs-shell { overflow: hidden; }
  .tabs-nav {
    display: flex; gap: 0.55rem; padding: 0.9rem 1rem 0.8rem; border-bottom: 1px solid #e4e4e4;
    align-items: center; flex-wrap: wrap;
  }
  .tabs-kicker { color: #666; font-size: 0.93rem; margin-right: auto; }
  .tab {
    appearance: none; border: 0; background: #f2f4f7; color: #445; cursor: pointer;
    font: inherit; font-weight: 600; padding: 0.48rem 0.82rem; border-radius: 999px;
  }
  .tab:hover { background: #e9eef7; }
  .tab[aria-selected="true"] { background: #e8f0fb; color: #1f4f7d; }
  .tab-panel { display: none; padding: 1rem 1rem 1.25rem; }
  .tab-panel.is-active { display: block; }
  .overview-only { padding-top: 0.1rem; }
  .section-copy { margin: 0.5rem 0 1.1rem; color: #666; line-height: 1.6; }
  .tree { padding: 1rem 1.05rem 1.15rem; }
  details { margin: 0.3rem 0 0.35rem 0; overflow: visible; background: transparent; border: 0; }
  details summary {
    list-style: none; cursor: pointer; padding: 0.42rem 0 0.42rem 1.35rem; position: relative;
    display: block; border-radius: 8px;
  }
  details summary::-webkit-details-marker { display: none; }
  details summary:hover { background: rgba(74,126,193,0.06); }
  details summary::before {
    content: "▸"; position: absolute; left: 0.3rem; top: 0.48rem; color: #888;
    transform-origin: center; transition: transform 120ms ease;
  }
  details[open] > summary::before { transform: rotate(90deg); }
  .summary-row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 0.9rem; align-items: start; }
  .summary-main { min-width: 0; }
  .summary-title {
    font-weight: 650; line-height: 1.4; font-family: ui-monospace, "SF Mono", Menlo, monospace;
  }
  .summary-sub { color: #666; font-size: 0.94rem; line-height: 1.55; margin-top: 0.16rem; }
  .summary-stats, .summary-bucket {
    font-size: 0.85rem; border-radius: 999px; padding: 0.2rem 0.58rem; white-space: nowrap;
  }
  .summary-stats { background: #eef3fb; color: #2a537f; }
  .summary-bucket { background: #f0f0f0; color: #555; }
  .bucket-feature { background: #e6f6ea; color: #1e6a30; }
  .bucket-fix { background: #fdecea; color: #9f2d21; }
  .bucket-refactor { background: #f2ebfb; color: #6c3ea2; }
  .bucket-test { background: #e8f7f3; color: #0d6e59; }
  .bucket-docs { background: #eaf2fb; color: #1d5f99; }
  .bucket-config { background: #fff4d6; color: #8a5a00; }
  .bucket-types { background: #eef1f4; color: #596674; }
  .bucket-other, .bucket-mixed { background: #f0f0f0; color: #555; }
  .details-body {
    margin-left: 0.78rem; padding: 0.22rem 0 0.6rem 1.45rem; border-left: 1px solid #d8d8d8;
  }
  .path-line { margin: 0 0 0.8rem; color: #666; line-height: 1.6; }
  .group-note { margin: 0.08rem 0 0.75rem; color: #555; line-height: 1.6; }
  ul.file-list, ul.flow-points { margin: 0; padding: 0; list-style: none; }
  ul.file-list li {
    margin: 0.7rem 0 0.85rem; padding-left: 2.25rem; position: relative;
  }
  ul.file-list li::before {
    content: "├──"; position: absolute; left: 0.15rem; top: 0.02rem; color: #8a8a8a;
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
  }
  ul.file-list li:last-child::before { content: "└──"; }
  .leaf-head { display: flex; flex-wrap: wrap; gap: 0.35rem 0.55rem; align-items: baseline; line-height: 1.45; }
  .leaf-path {
    font-weight: 600; font-family: ui-monospace, "SF Mono", Menlo, monospace;
    word-break: break-word; overflow-wrap: anywhere;
  }
  .leaf-note { color: #666; display: block; margin-top: 0.18rem; line-height: 1.58; }
  .indirect, .flow-summary, .size-card, .flow-shell { padding: 0.95rem 1rem; }
  .indirect-copy, .flow-summary-copy { margin: 0 0 0.85rem; color: #666; line-height: 1.6; }
  .indirect-list { display: grid; gap: 0.7rem; }
  .indirect-item {
    border: 1px solid #e5eaf2; border-radius: 10px; background: #f8fafc;
    padding: 0.75rem 0.9rem;
  }
  .indirect-head {
    display: flex; flex-wrap: wrap; gap: 0.35rem 0.55rem; align-items: baseline;
    margin-bottom: 0.12rem;
  }
  .indirect-label {
    display: inline-block; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.04em;
    text-transform: uppercase; color: #5c6470; background: #edf1f5; border-radius: 999px;
    padding: 0.14rem 0.48rem;
  }
  .flow-kicker { margin: 0 0 0.65rem; font-weight: 600; }
  ul.flow-points li { margin: 0.45rem 0; }
  .flow-shell { padding: 1rem 1rem 1.35rem; min-height: 62vh; }
  .flow-stage {
    display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.9rem;
    margin-bottom: 1rem;
  }
  .flow-card {
    background: #f6f8fb; border: 1px solid #e5eaf2; border-radius: 10px; padding: 0.85rem 0.95rem;
  }
  .flow-card h3 { margin: 0 0 0.35rem; font-size: 0.98rem; }
  .flow-card p { margin: 0; color: #666; font-size: 0.94rem; line-height: 1.55; }
  .diagram-frame {
    border: 1px solid #e3e7ee; border-radius: 12px; padding: 0.8rem 0.75rem 1rem;
    background: linear-gradient(180deg, #fcfdff 0%, #f8fafc 100%);
    overflow-x: auto; overflow-y: hidden;
  }
  .diagram-label { font-size: 0.88rem; font-weight: 600; color: #546579; margin: 0 0 0.45rem; }
  .size-card { margin-top: 1.25rem; }
  .size { color: #888; font-size: 0.9rem; }
  .nudge { background: #fff4d6; color: #7a5500; padding: 0.75rem 1rem; border-left: 3px solid #d68910; margin-top: 0.65rem; border-radius: 0 8px 8px 0; }
  code, pre { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 0.88rem; }
  code { background: #efefef; padding: 1px 4px; border-radius: 3px; }
  .muted { color: #888; }
  pre.mermaid {
    text-align: center; background: transparent;
    width: 1200px; min-width: 100%; margin: 0;
  }
  pre.mermaid svg { width: 100% !important; max-width: none !important; height: auto !important; }
  @media (max-width: 820px) {
    .summary-row { grid-template-columns: minmax(0, 1fr) auto; }
    .summary-bucket, .summary-stats { grid-column: 2; }
    .flow-stage { grid-template-columns: 1fr; }
    pre.mermaid { width: 980px; }
  }
</style>
</head>
<body>
<header>
  <h1>{{TITLE}}</h1>
  <div class="meta">{{META}}</div>
</header>

<div class="tldr"><strong>TL;DR.</strong> {{TLDR}}</div>

<div class="tabs-shell">
  {{TABS_NAV_OR_EMPTY}}

  <section class="{{OVERVIEW_PANEL_CLASS}}" id="panel-overview" role="tabpanel" aria-labelledby="tab-overview">
    {{TREE_SECTION}}

    {{INDIRECT_CONSUMERS_SECTION_OR_EMPTY}}

    {{FLOW_SUMMARY_SECTION_OR_EMPTY}}

    <div class="size-card"><div class="size">{{SIZE_INFO}}</div></div>
    {{NUDGE_OR_EMPTY}}
  </section>

  {{FLOW_PANEL_OR_EMPTY}}
</div>

{{SCRIPT_BLOCK_OR_EMPTY}}
</body>
</html>
```

## Script block example

Use lazy Mermaid rendering so hidden tabs do not produce broken SVG layout.

```html
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
  mermaid.initialize({
    startOnLoad: false,
    theme: "default",
    securityLevel: "loose",
    flowchart: { useMaxWidth: false, htmlLabels: true, nodeSpacing: 55, rankSpacing: 70 }
  });

  const tabs = Array.from(document.querySelectorAll('.tab'));
  const panels = Array.from(document.querySelectorAll('.tab-panel'));
  let flowRendered = false;

  async function ensureFlowRendered() {
    if (flowRendered) return;
    const diagrams = document.querySelectorAll('#panel-flow .mermaid');
    if (!diagrams.length) return;
    await mermaid.run({ nodes: diagrams });
    flowRendered = true;
  }

  async function activateTab(tab) {
    const targetId = tab.getAttribute('aria-controls');
    tabs.forEach((candidate) => {
      candidate.setAttribute('aria-selected', String(candidate === tab));
    });
    panels.forEach((panel) => {
      panel.classList.toggle('is-active', panel.id === targetId);
    });
    if (targetId === 'panel-flow') {
      await ensureFlowRendered();
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => { activateTab(tab); });
  });
</script>
```
