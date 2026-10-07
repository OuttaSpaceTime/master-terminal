#!/usr/bin/env bash
set -euo pipefail

dir="$1"
herdr="${HERDR_BIN_PATH:-herdr}"

case "$dir" in
  left)  key="alt+h" ;;
  down)  key="alt+j" ;;
  up)    key="alt+k" ;;
  right) key="alt+l" ;;
esac

if "$herdr" pane process-info --current \
  | jq -e '.result.process_info.foreground_processes[].name | select(test("^g?(view|l?n?vim?x?)(diff)?$"))' >/dev/null; then
  exec "$herdr" pane send-keys "$HERDR_PANE_ID" "$key"
fi

exec "$herdr" pane resize --direction "$dir" --current
