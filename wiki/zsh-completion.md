---
title: Zsh Completion
tags: [zsh, oh-my-zsh, completion]
created: 2026-04-24
updated: 2026-04-24
---

# Zsh Completion

- `home/dot_zshrc` used `zsh-autocomplete` for directory completion.
- That plugin is the likely source of the freeze/lag on deep `cd ../..` navigation.
- `fzf-tab` is the lighter replacement already installed in this environment and works with Oh My Zsh.
- If completion feels sluggish again, keep `fzf-tab` and avoid re-adding `zsh-autocomplete` unless you explicitly need its type-ahead behavior.
- In `fzf-tab`, multi-select is `Ctrl+Space` by default, then `Enter` to accept the selected items.
- For nested paths like `cd a/<tab>`, press `/` in the picker to continue completion inside the selected directory instead of opening a separate shell window.
