#!/bin/bash
INPUT=$(cat)

TITLE=$(echo "$INPUT" | jq -r '.title // "Claude Code"')
MSG=$(echo "$INPUT" | jq -r '.message // "Needs your input"')

notify-send "$TITLE" "$MSG" --icon=dialog-question
