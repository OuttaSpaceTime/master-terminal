#!/bin/bash
# Set kitty tab icon based on Claude Code session state.
# Usage: set-tab-icon.sh <running|permission|finished|clear>
#
# Per-window state files in /tmp/claude-tab-state/ track each split's
# state. On every update the script aggregates all siblings in the same
# kitty tab and displays all distinct icons in priority order: ❓️⚡️✅
#
# Only sibling window IDs reported by kitty @ ls are considered,
# so orphaned state files from dead windows are naturally ignored.
#
# On clear, own state is removed and remaining siblings are
# re-aggregated so their icons survive.
#
# Manual title changes (Ctrl+Shift+Alt+T) are preserved — icons
# are stripped and re-prepended around the user-chosen base title.

STATE_DIR="/tmp/claude-tab-state"
STATE="$1"
WINDOW_ID="${KITTY_WINDOW_ID:-}"

[[ -z "$WINDOW_ID" ]] && exit 0

STATE_FILE="$STATE_DIR/$WINDOW_ID.state"

# Skip redundant updates (PreToolUse fires on every tool call).
# Never skip "clear" — it must always run.
if [[ "$STATE" != "clear" && -f "$STATE_FILE" ]] && [[ "$(<"$STATE_FILE")" == "$STATE" ]]; then
  exit 0
fi

# Outputs two lines: 1) base title (icon prefix stripped), 2) space-separated
# window IDs of all windows in the same tab.
_tab_info() {
  export KITTY_WID="$WINDOW_ID"
  kitty @ ls 2>/dev/null | python3 -c "
import json,sys,re,os
wid=int(os.environ['KITTY_WID'])
for o in json.load(sys.stdin):
 for t in o['tabs']:
  wids=[w['id'] for w in t.get('windows',[])]
  if wid in wids:
   title=t['title']
   print(re.sub(r'^(?:[\u26a1\u2753\u2705]\ufe0f?)+\s*','',title))
   print(' '.join(str(w) for w in wids))
   exit()
" 2>/dev/null
}

# Write own state first (before reading siblings) so concurrent
# updates from other splits always see fresh data.
[[ -d "$STATE_DIR" ]] || mkdir -p "$STATE_DIR"
if [[ "$STATE" == "clear" ]]; then
  rm -f "$STATE_FILE"
else
  echo "$STATE" > "$STATE_FILE"
fi

INFO=$(_tab_info)
BASE=$(head -1 <<< "$INFO")
read -r -a SIBLINGS <<< "$(tail -1 <<< "$INFO")"

# Collect distinct states from all live siblings.
# Only windows present in kitty @ ls are checked — orphans ignored.
HAS_PERMISSION=0 HAS_RUNNING=0 HAS_FINISHED=0
for SID in "${SIBLINGS[@]}"; do
  SFILE="$STATE_DIR/$SID.state"
  [[ -f "$SFILE" ]] || continue
  case "$(<"$SFILE")" in
    permission) HAS_PERMISSION=1 ;;
    running)    HAS_RUNNING=1 ;;
    finished)   HAS_FINISHED=1 ;;
  esac
done

# Build icon string: all distinct states in priority order
ICONS=""
(( HAS_PERMISSION )) && ICONS+=$'\xe2\x9d\x93\xef\xb8\x8f'   # ❓️
(( HAS_RUNNING ))    && ICONS+=$'\xe2\x9a\xa1\xef\xb8\x8f'   # ⚡️
(( HAS_FINISHED ))   && ICONS+=$'\xe2\x9c\x85'                # ✅

if [[ -n "$ICONS" ]]; then
  kitty @ set-tab-title --match "window_id:$WINDOW_ID" "${ICONS} ${BASE}" 2>/dev/null
else
  kitty @ set-tab-title --match "window_id:$WINDOW_ID" "$BASE" 2>/dev/null
fi
