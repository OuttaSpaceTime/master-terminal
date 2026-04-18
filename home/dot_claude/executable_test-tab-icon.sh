#!/bin/bash
# Tests for set-tab-icon.sh — run inside a kitty terminal.
# Exercises all states, multi-split icon composition, clear
# re-aggregation, and orphan resilience.

set -euo pipefail

SCRIPT="${1:-$HOME/.claude/set-tab-icon.sh}"
STATE_DIR="/tmp/claude-tab-state"
WID="${KITTY_WINDOW_ID:?Must run inside kitty}"
PASS=0 FAIL=0

# Find a sibling window ID in the same tab (for multi-split tests)
SIBLING=$(kitty @ ls 2>/dev/null | python3 -c "
import json,sys
wid=$WID
for o in json.load(sys.stdin):
 for t in o['tabs']:
  wids=[w['id'] for w in t.get('windows',[])]
  if wid in wids:
   for w in wids:
    if w != wid: print(w); exit()
" 2>/dev/null)

_get_title() {
  kitty @ ls 2>/dev/null | python3 -c "
import json,sys
wid=$WID
for o in json.load(sys.stdin):
 for t in o['tabs']:
  for w in t.get('windows',[]):
   if w['id']==wid: print(t['title']); exit()
" 2>/dev/null
}

_reset() {
  rm -rf "$STATE_DIR"
  kitty @ set-tab-title --match "window_id:$WID" "test-tab" 2>/dev/null
}

_assert() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $label"
    ((++PASS))
  else
    echo "  FAIL: $label"
    echo "    expected: '$expected'"
    echo "    actual:   '$actual'"
    ((++FAIL))
  fi
}

echo "=== set-tab-icon.sh tests ==="
echo "Script: $SCRIPT"
echo "Window: $WID, Sibling: ${SIBLING:-none}"
echo ""

# --- Single session states ---
echo "Single session:"
_reset
bash "$SCRIPT" running
_assert "running → ⚡️" "⚡️ test-tab" "$(_get_title)"

rm -f "$STATE_DIR/$WID.state"
bash "$SCRIPT" permission
_assert "permission → ❓️" "❓️ test-tab" "$(_get_title)"

rm -f "$STATE_DIR/$WID.state"
bash "$SCRIPT" finished
_assert "finished → ✅" "✅ test-tab" "$(_get_title)"

# --- Redundancy skip ---
echo ""
echo "Redundancy skip:"
_reset
bash "$SCRIPT" running
kitty @ set-tab-title --match "window_id:$WID" "manually renamed" 2>/dev/null
bash "$SCRIPT" running  # should skip (state unchanged)
_assert "skip preserves manual rename" "manually renamed" "$(_get_title)"

# --- Clear ---
echo ""
echo "Clear:"
_reset
bash "$SCRIPT" running
bash "$SCRIPT" clear
_assert "clear restores bare title" "test-tab" "$(_get_title)"
_assert "clear removes state file" "" "$(ls "$STATE_DIR/$WID.state" 2>/dev/null)"

# --- Manual rename mid-session ---
echo ""
echo "Manual rename survives state change:"
_reset
bash "$SCRIPT" running
kitty @ set-tab-title --match "window_id:$WID" "⚡️ my-custom" 2>/dev/null
rm -f "$STATE_DIR/$WID.state"
bash "$SCRIPT" finished
_assert "rename preserved" "✅ my-custom" "$(_get_title)"

# --- Multi-split tests (requires sibling window) ---
if [[ -n "$SIBLING" ]]; then
  echo ""
  echo "Multi-split icons (sibling=$SIBLING):"

  # running + finished → both icons
  _reset
  mkdir -p "$STATE_DIR"
  echo "finished" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" running
  _assert "running + finished → ⚡️✅" "⚡️✅ test-tab" "$(_get_title)"

  # permission + running → both icons, permission first
  _reset
  mkdir -p "$STATE_DIR"
  echo "permission" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" running
  _assert "permission + running → ❓️⚡️" "❓️⚡️ test-tab" "$(_get_title)"

  # permission + finished → both icons
  _reset
  mkdir -p "$STATE_DIR"
  echo "permission" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" finished
  _assert "permission + finished → ❓️✅" "❓️✅ test-tab" "$(_get_title)"

  # both same state → single icon
  _reset
  mkdir -p "$STATE_DIR"
  echo "running" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" running
  _assert "both running → single ⚡️" "⚡️ test-tab" "$(_get_title)"

  _reset
  mkdir -p "$STATE_DIR"
  echo "finished" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" finished
  _assert "both finished → single ✅" "✅ test-tab" "$(_get_title)"

  # --- Clear re-aggregates siblings ---
  echo ""
  echo "Clear re-aggregates:"

  _reset
  mkdir -p "$STATE_DIR"
  echo "running" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" running
  bash "$SCRIPT" clear
  _assert "clear with sibling running → ⚡️" "⚡️ test-tab" "$(_get_title)"

  _reset
  mkdir -p "$STATE_DIR"
  echo "permission" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" finished
  bash "$SCRIPT" clear
  _assert "clear with sibling permission → ❓️" "❓️ test-tab" "$(_get_title)"

  _reset
  mkdir -p "$STATE_DIR"
  echo "finished" > "$STATE_DIR/$SIBLING.state"
  bash "$SCRIPT" running
  bash "$SCRIPT" clear
  _assert "clear with sibling finished → ✅" "✅ test-tab" "$(_get_title)"

  _reset
  mkdir -p "$STATE_DIR"
  bash "$SCRIPT" running
  bash "$SCRIPT" clear
  _assert "clear with no sibling state → bare" "test-tab" "$(_get_title)"

  # --- Orphan resilience ---
  echo ""
  echo "Orphan resilience:"
  _reset
  mkdir -p "$STATE_DIR"
  echo "permission" > "$STATE_DIR/99999999.state"  # fake dead window
  bash "$SCRIPT" running
  _assert "orphan ignored → ⚡️" "⚡️ test-tab" "$(_get_title)"
  rm -f "$STATE_DIR/99999999.state"

  rm -f "$STATE_DIR/$SIBLING.state"
else
  echo ""
  echo "SKIP: multi-split tests (no sibling window in tab)"
fi

# --- Non-kitty environment ---
echo ""
echo "Non-kitty environment:"
(unset KITTY_WINDOW_ID; bash "$SCRIPT" running 2>/dev/null)
_assert "exits silently without KITTY_WINDOW_ID" "0" "$?"

# --- Restore ---
_reset
kitty @ set-tab-title --match "window_id:$WID" "" 2>/dev/null

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
exit "$FAIL"
