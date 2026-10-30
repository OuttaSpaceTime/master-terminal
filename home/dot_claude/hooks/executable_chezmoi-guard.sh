#!/usr/bin/env bash
# PostToolUse hook: block edits to chezmoi-managed deployed files and
# redirect Claude to the chezmoi source path instead.
#
# Exit codes:
#   0 - allow edit (not managed / not applicable / chezmoi unavailable)
#   2 - block edit; stderr is fed back to the model

set -u

CHEZMOI_SOURCE_DIR="/home/felix/Code/Misc/master-terminal/home"

# Read JSON payload from stdin
payload="$(cat)"

# Extract tool_name and file_path. Prefer jq, fall back to python3.
extract() {
  local field="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r "$field // empty" 2>/dev/null
  else
    printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
# Translate a trivial subset of jq path like ".tool_name" or ".tool_input.file_path"
path = sys.argv[1].lstrip(".")
cur = data
for part in path.split("."):
    if part.endswith(" // empty"):
        part = part.split(" ")[0]
    if isinstance(cur, dict) and part in cur:
        cur = cur[part]
    else:
        sys.exit(0)
if cur is None:
    sys.exit(0)
print(cur)
' "$field"
  fi
}

tool_name="$(extract '.tool_name')"
file_path="$(extract '.tool_input.file_path')"

# Only care about edit-shaped tools
case "$tool_name" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

# No file_path -> nothing to check
[ -n "${file_path:-}" ] || exit 0

# chezmoi not installed -> don't break anything
command -v chezmoi >/dev/null 2>&1 || exit 0

# If the file is already inside the chezmoi source tree, allow it.
case "$file_path" in
  "$CHEZMOI_SOURCE_DIR"/*) exit 0 ;;
esac

# Ask chezmoi if there is a source file for this target path.
source_path="$(chezmoi -S "$CHEZMOI_SOURCE_DIR" source-path "$file_path" 2>/dev/null)" || exit 0
[ -n "$source_path" ] || exit 0

# A chezmoi source exists -> block and redirect.
cat >&2 <<EOF
Blocked: $file_path is a chezmoi-managed deployed file.

Edit the chezmoi source instead:
  $source_path

Then deploy with:
  chezmoi -S $CHEZMOI_SOURCE_DIR apply

(Direct edits to deployed files will be overwritten on the next chezmoi apply.)
EOF
exit 2
