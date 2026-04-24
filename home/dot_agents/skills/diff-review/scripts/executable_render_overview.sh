#!/usr/bin/env bash
# render_overview.sh — open a self-contained HTML overview produced by /diff-review CP1.
# Detached launch via `setsid -f`, error log under /tmp, never blocks the caller. The
# HTML itself is written by the skill — this script only opens it.
#
# Usage: render_overview.sh <input.html> [--open]
#
# Without --open the script just validates the file exists and prints its absolute path.
# With --open the script attempts a detached open; if no display server is reachable, it
# falls back to printing the absolute path and a file:// URI and exits 0.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: render_overview.sh <input.html> [--open]" >&2
  exit 2
fi

INPUT="$1"
shift || true

OPEN=0
for arg in "$@"; do
  case "$arg" in
    --open) OPEN=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [[ "${INPUT##*.}" != "html" ]]; then
  echo "expected an .html file, got: $INPUT" >&2
  exit 2
fi
if [[ ! -f "$INPUT" ]]; then
  echo "file not found: $INPUT" >&2
  exit 2
fi

ABS_PATH="$(readlink -f "$INPUT")"
FILE_URI="file://$ABS_PATH"

if [[ "$OPEN" -eq 0 ]]; then
  echo "$ABS_PATH"
  exit 0
fi

# Headless detection: if neither $DISPLAY nor $WAYLAND_DISPLAY is set, no opener will
# work on most desktop environments. Print the path and exit cleanly so the caller can
# tell the user how to view it.
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "no display server detected; open this manually:"
  echo "  $FILE_URI"
  exit 0
fi

LOG=/tmp/diff-overview-open.log

# Prefer xdg-open (browser will be the user's default html handler). setsid -f detaches
# fully so the script returns immediately and the browser keeps running. The `|| true`
# ensures a missing opener doesn't propagate a non-zero exit.
if command -v xdg-open >/dev/null 2>&1; then
  setsid -f sh -c 'xdg-open "$1"' _ "$ABS_PATH" >"$LOG" 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  setsid -f sh -c 'open "$1"' _ "$ABS_PATH" >"$LOG" 2>&1 || true
else
  echo "no opener (xdg-open / open) found; open this manually:"
  echo "  $FILE_URI"
  exit 0
fi

echo "opened $FILE_URI"
