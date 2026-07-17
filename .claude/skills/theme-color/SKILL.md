---
name: theme-color
description: >
  Pick and apply a new theme color for master-terminal's light dotfiles theme by building
  a live HTML artifact that renders real candidates against the actual kitty background and
  font, with WCAG contrast ratios computed live — never eyeballed or guessed from a
  screenshot. Trigger whenever the user says a terminal/diff/syntax color is "hard to
  read", asks to "suggest a different green/color/accent", wants to "check contrast" for
  the kitty/nvim/statusline theme, says "I don't like these options" or "any other
  options" while reviewing color candidates, or wants a chosen color applied everywhere
  it's used (kitty, nvim, fzf, statusline, p10k) via chezmoi. Also covers "is our font
  good/bad for light mode" and "can we use a bolder font" questions that come up during
  the same readability discussion.
---

# Theme Color

Pick a readable color for master-terminal's light theme, verify it against real values,
then apply it everywhere the old one was used.

## Why grounding matters

Contrast is a math problem, not a taste problem — "does this look readable" from memory
or a screenshot is unreliable because rendering differs between the browser previewing a
hex code and kitty's own font hinting/anti-aliasing. Every candidate must be checked
against the *actual* deployed background hex and rendered in the *actual* configured
font, and the contrast ratio must be computed with the real WCAG formula, not guessed.

## Step 1 — Read real values first

Pull current values straight from the chezmoi **source** (never the deployed
`~/.config/...` copy):
- `home/private_dot_config/kitty/current-theme.conf` — `background`, `foreground`, and the
  `color0`-`color15` ANSI table (the color being replaced lives here).
- `home/private_dot_config/kitty/kitty.conf` — `font_family`, `bold_font`, `font_size`.
- `wiki/light-theme-palette.md` — the palette table and, critically, the "Where each color
  lives" section listing every other file that references a given hex (nvim colorscheme,
  statusline script, fzf, p10k). Read this before proposing anything, and update it once a
  color changes.

## Step 2 — Build the comparison artifact

Load the `artifact-design` skill, then write a self-contained HTML file (scratchpad
directory) and publish it with the Artifact tool:
- Pin the preview background to the *exact* real hex (e.g. `#fafafa`) — this is the one
  thing that must never adapt to the artifact viewer's light/dark theme, since the whole
  point is testing against the real fixed terminal background.
- Render each candidate as a realistic snippet from the tool it's actually used in (a git
  diff hunk for diff colors, a prompt segment for p10k, etc.) using the real font-family
  and font-weight — match the *actual* rendering (don't bold a "+" line if the real diff
  pager doesn't bold it; verify against a screenshot if the user provides one).
- Compute WCAG contrast ratio live in JS (relative luminance formula) against the pinned
  background for every candidate, and show a AA (>=4.5:1) / AAA (>=7:1) / FAIL badge — this
  is the actual proof, not a claim.
- Always include the current value(s) as a baseline card so the user can compare
  candidates against what they already have.
- Iterate in place: when the user reacts ("don't love these", "any other options", "what
  about X"), add more candidate cards to the SAME array and republish to the SAME file
  path so the URL stays stable — don't start a new artifact per round.

## Step 3 — Verify numbers, don't eyeball them

If the user asks what AA/AAA means, or wants exact ratios listed in chat (not just in the
artifact), compute them with a small script rather than restating the JS math by hand —
arithmetic mistakes are easy, and the whole premise of this skill is that the numbers are
checked, not asserted. A short Python script (relative luminance → contrast ratio), run
through the normal task-script flow, is enough — reuse it across rounds by editing its
candidate dict rather than rewriting it from scratch each time.

## Step 4 — Apply the choice everywhere

Once the user picks a hex:
1. Re-check `wiki/light-theme-palette.md`'s "Where each color lives" map (Step 1) and
   `grep -rn "<old-hex>" home/ wiki/` to find every reference — don't rely on memory of
   what you touched last time, the same green can appear in kitty, nvim, the statusline
   script, and fzf's `FZF_DEFAULT_OPTS`.
2. Edit only the chezmoi **source** files under `home/`, one at a time.
3. `chezmoi -S home diff <target>` scoped to just the files you touched — confirm each
   diff is exactly the intended one-line hex swap before applying.
   Check for unrelated drift first (`chezmoi -S home diff` with no path) so a scoped
   apply doesn't skip a conflict, and don't deploy unrelated pending changes the user
   didn't ask for.
4. `chezmoi -S home apply <target>`, same scoping.
5. Update the wiki table's hex + role description to match, and bump its `updated` date.
6. Remind the user which running programs need a restart to pick up the new color (kitty:
   `ctrl+shift+F5`; nvim: restart; zsh/fzf/p10k: new shell) — stale instances are the
   biggest source of "it didn't change" confusion, per the wiki's own gotchas section.

## Notes

- Don't touch `color10`/"bright" variants unless asked — normal and bright ANSI slots are
  separate colors serving separate purposes; fixing one doesn't imply fixing the other.
  Flag it if it also fails contrast, but let the user decide whether it's in scope.
- Font weight and color contrast are independent axes — a bolder weight doesn't raise a
  WCAG ratio. If asked about bolder fonts, check what's actually installed
  (`fc-list | grep -i <font family>`) rather than assuming a family ships a heavier weight
  than what's already configured.
