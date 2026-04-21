#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  render_and_open.sh <input.d2> [--open]

Options:
  --open   Open rendered PNG and SVG after generation (detached).
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

input=""
open_after=0

for arg in "$@"; do
  case "$arg" in
    --open)
      open_after=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$input" ]]; then
        input="$arg"
      else
        echo "Unexpected argument: $arg" >&2
        usage
        exit 1
      fi
      ;;
  esac
done

if [[ -z "$input" ]]; then
  echo "Missing input .d2 file." >&2
  usage
  exit 1
fi

if [[ ! -f "$input" ]]; then
  echo "Input file not found: $input" >&2
  exit 1
fi

base="${input%.d2}"
if [[ "$base" == "$input" ]]; then
  echo "Input must end with .d2: $input" >&2
  exit 1
fi

svg="${base}.svg"
png="${base}.png"

run_d2() {
  if command -v d2 >/dev/null 2>&1; then
    d2 "$1" "$2"
  else
    npx -y terrastruct-d2-bin "$1" "$2"
  fi
}

run_d2 "$input" "$svg"
run_d2 "$input" "$png"

echo "Rendered: $svg"
echo "Rendered: $png"

if [[ "$open_after" -eq 1 ]]; then
  if command -v eog >/dev/null 2>&1; then
    setsid -f eog "$png" "$svg" >/tmp/d2-open.log 2>&1 || true
  else
    setsid -f xdg-open "$png" >/tmp/d2-open.log 2>&1 || true
    setsid -f xdg-open "$svg" >>/tmp/d2-open.log 2>&1 || true
  fi
  echo "Open requested. Log: /tmp/d2-open.log"
fi
