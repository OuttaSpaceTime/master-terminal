---
name: write-check
description: Open the local Write Check app (markdown grammar, spelling and AI-style checker for German and English) and collaborate on a text. Use when the user wants to check, improve, or draft a text, wants writing feedback (logic, clarity, style), or types /write-check. Arguments are optional and may be the text itself or instructions on what to write.
---

# Write Check

Local Next.js app at `/home/felix/Code/Misc/write-check`, served on **http://localhost:3456**. It checks markdown text for grammar/spelling (LanguageTool, German + English), AI-writing patterns (rule catalog + document statistics), and shows Claude review notes. The goal is not only fixing texts but helping Felix improve as a writer — feedback must always explain *why* something is a problem.

## Start the services

1. Dev server: `curl -sf http://localhost:3456/api/review >/dev/null 2>&1` — if this fails, run `npm run dev` in the app directory as a background task and wait until the URL responds.
2. LanguageTool: `docker start languagetool 2>/dev/null || docker run -d --name languagetool -p 8010:8010 erikvl87/languagetool`

## One directory per check

Every new check gets its own directory inside the app: `data/checks/<YYYY-MM-DD>-<slug>/`, holding `document.md` and `review.json`. The date is today, the slug a short kebab-case name for the topic (`2026-09-10-hyprland-post`, `2026-09-10-knowledge-card-draft`). Never write into `data/document.md` — that is the old shared scratch document.

- Pick the path once at the start of a check and keep using it for the rest of the conversation: further edits, rewrites and review notes go into that same directory.
- A new `/write-check` invocation, or a text that is plainly a different piece of writing, gets a new directory. Earlier checks stay readable where they are.
- Before picking a slug, `ls data/checks/` — if the user is continuing a text you already worked on, reuse its directory instead of making a near-duplicate.

Open the app on that check:

```
xdg-open 'http://localhost:3456/?doc=checks/<YYYY-MM-DD>-<slug>'
```

Tell the user the relative path you chose, so they can reopen it later.

## The document

- The single source of truth is `document.md` inside the check directory. The browser editor and this file sync automatically every ~2.5 s (last writer wins; the app also autosaves edits made in the browser back to this file).
- `/write-check <text>` → Write the given text to `document.md`, then open the app on that check.
- `/write-check <instructions>` → Draft the text yourself, write it to `document.md`, then open the app. When drafting: be concrete and specific, avoid the AI-boilerplate the app flags (delve, tapestry, "plays a pivotal role", "in today's digital age", formulaic transitions, em-dash chains, uniform sentence rhythm — and the German equivalents: "in der heutigen digitalen Welt", "spielt eine entscheidende Rolle", "zudem"-chains, Fazit-Formeln). Write like a person with an opinion, not a brochure.
- `/write-check` with no arguments → ask which text this is about, or start an empty check directory and open the app on it.
- When the user asks you to correct or rewrite something: edit the check's `document.md` directly with the Edit tool; the browser picks it up automatically.

## Giving feedback (review notes)

Write your feedback to `review.json` next to the document in the same check directory. Within ~2.5 s the UI shows each note, labeled "Claude", under the cell (the editor box) that holds its quote. Format:

```json
{
  "notes": [
    {
      "quote": "exact substring copied from document.md",
      "scope": "optional: \"cell\" or \"missing\"",
      "title": "Contradicts earlier claim",
      "message": "What is wrong, in one or two sentences.",
      "explanation": "Why this is a problem — teach the underlying writing principle.",
      "suggestion": "Optional concrete rewrite.",
      "severity": "warning"
    }
  ]
}
```

Rules:
- `quote` must be copied verbatim from the current `document.md` so the note anchors to the right spot (it becomes clickable and underlined in the editor). Notes anchor to the FIRST occurrence of the quote — if the phrase appears more than once, extend the quote until it is unique.
- Pick where a note lives:
  - no `scope`: the note is about the quoted words, which get underlined.
  - `"scope": "cell"`: the note is about the whole paragraph that holds the quote ("this paragraph has no point"). Quote a few words from it; nothing is underlined.
  - `"scope": "missing"`: something is missing right after the quote (a step, a number, a transition). The note appears as a dashed "Something is missing here" slot after that paragraph.
  - no `quote`: the note appears in the "Whole text" box above the first cell. Use it only for a point no quote can carry: the order of the sections, a template or audience the whole text must fit, a decision from the chat that has no place in the text. A missing section or counter-argument usually has a spot (after the claim it should answer, between the sections it belongs between) and goes there as a `"missing"` note.
- Never put a point in the "Whole text" box that is anchored, or could be. No overview of the anchored notes ("Where to shorten: merge the paragraphs under 3, shrink the explanation under 4, end with a question"), and no "this happens throughout" note for a problem you can point to.
- When one problem shows up in several places, put a note at each place. The first carries the full `message` and `explanation`. Each further one keeps the same `title`, says in `message` that it is the same problem as the note on "<first note's quote>", gives a `suggestion` for that line only, and has no `explanation`.
- `severity`: `"error"` (broken logic, factual contradiction), `"warning"` (unclear, weak argument), `"info"` (style polish).
- Review for: **logic soundness** (does each claim follow from its support? non-sequiturs? contradictions? unsupported leaps?), **clarity** (is the point of each section stated and reachable? undefined jargon? buried lede?), and anything discussed in the current chat — feedback the user gave you or conclusions from your discussion belong in the notes too, so the app shows one consolidated list. Anchor them like any other note.
- Every note must teach: always fill `explanation` with the principle, not just the fix. The only exception is a further note on a repeated problem, described in the rule above.
- After writing `review.json`, run this in the app directory. It prints every quote that is not found exactly once in the document, because a quote that isn't found lands its note in the "Whole text" box. Fix each one it prints:

  ```
  node -e 'const fs=require("fs"),d=process.argv[1],t=fs.readFileSync(d+"/document.md","utf8");for(const {quote:q} of JSON.parse(fs.readFileSync(d+"/review.json","utf8")).notes)if(q&&t.split(q).length!==2)console.log(t.includes(q)?"not unique:":"not found:",q)' data/checks/<YYYY-MM-DD>-<slug>
  ```
- Replace the whole file each time; write `{"notes": []}` to clear. Notes whose quote no longer matches the text move to the "Whole text" box with a "quoted words are no longer in the text" line.
- The user ticks notes off as done. `done.json` in the check directory lists them: Claude notes as `claude|<title>|<quote>`, app findings as `<ruleId>|<flagged words>`. Read it before writing a new review and don't repeat a note the user already closed unless the problem came back in a new form; keep the same `title` and `quote` for a note you carry over, or its tick is lost.
- `cells.json` is the app's own record of how the user split and merged cells. Don't edit it.

## Reading the app's own findings

To see what the automated checks currently flag (grammar, spelling, AI patterns, metrics), run in the app directory:

```
node scripts/print-check.mjs --doc=checks/<YYYY-MM-DD>-<slug>
```

Append `de-DE` or `en-US` to force the language. Use this before discussing the text so your feedback and the app's findings don't contradict each other, and to answer questions like "why is this flagged?".

## Technical words the spell checker doesn't know

Every time you write or change `document.md`, run `print-check` afterwards and go through the spelling findings. LanguageTool flags tool, library and project names it has no dictionary entry for (`esbuild`, `oxc`, `rolldown`, `Angular`, `Vite`). These are noise, not mistakes.

- Add each flagged word that is clearly a technical name, spelled the way its project spells it, to `data/words.json` (`{"words": [...]}`). Copy the flagged span exactly as it appears in the text. Matching ignores case.
- The file is shared by every check. Keep the words already in it, and create it if it doesn't exist.
- Never add a real misspelling, an ordinary word, or a misspelled technical name (`esbiuld`). When you're unsure whether a word is a technical name, leave the finding for the user.
- The app reloads the list every ~2.5 s and runs the check again, so the findings disappear without a page reload. Run `print-check` once more to confirm only real spelling findings remain.
