#!/bin/bash

input=$(cat)
dir=$(echo "$input" | jq -r '.workspace.current_dir // empty' 2>/dev/null)
[ -z "$dir" ] && dir=$(pwd)

# Check if waiting for input/permission (common field indicators)
waiting=$(echo "$input" | jq -r '.session.waiting_for_input // .awaiting_input // .requires_permission // .requires_action // empty' 2>/dev/null)
waiting_icon=""
if [ "$waiting" = "true" ] || [ -n "$waiting" ]; then
  waiting_icon="󰑐 "  # Thinking icon from nerd font
fi

# Colors
CYAN=$'\033[38;2;12;110;116m'    # teal    #0c6e74
GREEN=$'\033[38;2;0;99;54m'      # green   #006336
BLUE=$'\033[38;2;10;79;208m'     # blue    #0a4fd0
YELLOW=$'\033[38;2;184;74;0m'    # orange  #b84a00
RED=$'\033[38;2;189;0;38m'       # red     #bd0026
WHITE=$'\033[38;2;28;30;42m'     # text    #1c1e2a
MAGENTA=$'\033[38;2;200;31;158m' # pink    #c81f9e
DIM=$'\033[38;2;140;144;160m'    # gray    #8c90a0
RESET=$'\033[00m'

# Debug: log full raw input for field inspection
echo "$input" > /tmp/claude-statusline-debug.json

# Model: extract tier and version from model ID (e.g. claude-sonnet-4-6 → Sonnet 4.6)
model_id=$(echo "$input" | jq -r '.model.id // empty' 2>/dev/null)
case "$model_id" in
  *opus*)   model_tier="Opus"   ;;
  *sonnet*) model_tier="Sonnet" ;;
  *haiku*)  model_tier="Haiku"  ;;
  *)        model_tier=""       ;;
esac
# Extract version digits after the tier name: e.g. claude-sonnet-4-6 → 4-6 → 4.6
# Strip leading "claude-<tier>-" prefix, then take only the first two numeric segments
# (handles trailing date suffixes like 20251001 in haiku IDs)
model_version=""
if [ -n "$model_tier" ]; then
  tier_lower=$(echo "$model_tier" | tr '[:upper:]' '[:lower:]')
  after_tier="${model_id#*${tier_lower}-}"
  # Extract major.minor only (two numeric groups separated by a dash)
  major=$(echo "$after_tier" | cut -d'-' -f1)
  minor=$(echo "$after_tier" | cut -d'-' -f2)
  if [[ "$major" =~ ^[0-9]+$ ]] && [[ "$minor" =~ ^[0-9]+$ ]] && [ "${#minor}" -le 2 ]; then
    model_version="${major}.${minor}"
  elif [[ "$major" =~ ^[0-9]+$ ]]; then
    model_version="${major}"
  fi
fi

# Reasoning effort: live per-session level (low/medium/high/xhigh/max)
effort=$(echo "$input" | jq -r '.effort.level // empty' 2>/dev/null)

# Context window usage % (green < 50, yellow < 80, red >= 80)
ctx_pct=$(printf "%.0f" "$(echo "$input" | jq -r '.context_window.used_percentage // 0' 2>/dev/null)" 2>/dev/null || echo "0")
if [ "$ctx_pct" -gt 80 ] 2>/dev/null; then
  ctx_color="$RED"
elif [ "$ctx_pct" -gt 50 ] 2>/dev/null; then
  ctx_color="$YELLOW"
else
  ctx_color="$GREEN"
fi

# Context window max size formatted as 1M / 0.2M / 200K
ctx_size_raw=$(echo "$input" | jq -r '.context_window.context_window_size // empty' 2>/dev/null)
ctx_size_fmt=""
if [ -n "$ctx_size_raw" ] && [[ "$ctx_size_raw" =~ ^[0-9]+$ ]]; then
  if [ "$ctx_size_raw" -ge 1000000 ]; then
    # Round to nearest 0.1M using awk; drop trailing .0
    ctx_size_fmt=$(awk -v n="$ctx_size_raw" 'BEGIN {
      v = int((n / 1000000) * 10 + 0.5) / 10
      if (v == int(v)) printf "%dM", int(v)
      else printf "%.1fM", v
    }')
  elif [ "$ctx_size_raw" -ge 1000 ]; then
    ctx_size_fmt=$(awk -v n="$ctx_size_raw" 'BEGIN { printf "%dK", int(n/1000 + 0.5) }')
  else
    ctx_size_fmt="${ctx_size_raw}"
  fi
fi

# Git
branch=""
git_flags=""
if git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
  raw_branch=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null)
  branch="$raw_branch"
  git_dir=$(git -C "$dir" rev-parse --absolute-git-dir 2>/dev/null)

  # Mid-operation state
  if [ -f "$git_dir/MERGE_HEAD" ]; then
    branch="${branch}(merge)"
  elif [ -f "$git_dir/CHERRY_PICK_HEAD" ]; then
    branch="${branch}(cherry-pick)"
  elif [ -f "$git_dir/REVERT_HEAD" ]; then
    branch="${branch}(revert)"
  elif [ -d "$git_dir/rebase-merge" ] || [ -d "$git_dir/rebase-apply" ]; then
    branch="${branch}(rebase)"
  fi

  # Staged (+), unstaged (*), untracked (?)
  git -C "$dir" diff --cached --quiet 2>/dev/null || git_flags="${git_flags}+"
  git -C "$dir" diff --quiet 2>/dev/null || git_flags="${git_flags}*"
  [ -n "$(git -C "$dir" ls-files --others --exclude-standard 2>/dev/null | head -1)" ] && git_flags="${git_flags}?"

  # Ahead/behind remote
  if [ -n "$raw_branch" ] && [ "$raw_branch" != "HEAD" ]; then
    ahead=$(git -C "$dir" rev-list --count "${raw_branch}@{upstream}..HEAD" 2>/dev/null)
    behind=$(git -C "$dir" rev-list --count "HEAD..${raw_branch}@{upstream}" 2>/dev/null)
    [ "${ahead:-0}" -gt 0 ] && git_flags="${git_flags}↑${ahead}"
    [ "${behind:-0}" -gt 0 ] && git_flags="${git_flags}↓${behind}"
  fi
fi

# Shorten path: ~/…/last-two-segments if under home, else last two segments
home=$(eval echo "~")
if [[ "$dir" == "$home"/* ]]; then
  rel="${dir#"$home"/}"
  IFS='/' read -ra segs <<< "$rel"
  n=${#segs[@]}
  if [ "$n" -le 2 ]; then
    dir="~/$rel"
  else
    dir="~/…/${segs[$((n-2))]}/${segs[$((n-1))]}"
  fi
fi

# Rate limits (Claude.ai subscription quota)
five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty' 2>/dev/null)
week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty' 2>/dev/null)

quota_str=""
if [ -n "$five_pct" ]; then
  five_fmt=$(printf "%.0f" "$five_pct" 2>/dev/null || echo "?")
  if [ "$five_fmt" -gt 80 ] 2>/dev/null; then rl_color="$RED"
  elif [ "$five_fmt" -gt 50 ] 2>/dev/null; then rl_color="$YELLOW"
  else rl_color="$GREEN"
  fi
  five_resets_at=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty' 2>/dev/null)
  five_reset_str=""
  if [ -n "$five_resets_at" ]; then
    five_reset_fmt=$(date -d "@${five_resets_at}" +%H:%M 2>/dev/null || date -r "${five_resets_at}" +%H:%M 2>/dev/null)
    [ -n "$five_reset_fmt" ] && five_reset_str="↺${five_reset_fmt}"
  fi
  quota_str="${rl_color}5h:${five_fmt}%${five_reset_str}${RESET}"
fi
if [ -n "$week_pct" ]; then
  week_fmt=$(printf "%.0f" "$week_pct" 2>/dev/null || echo "?")
  if [ "$week_fmt" -gt 80 ] 2>/dev/null; then rl_color="$RED"
  elif [ "$week_fmt" -gt 50 ] 2>/dev/null; then rl_color="$YELLOW"
  else rl_color="$GREEN"
  fi
  [ -n "$quota_str" ] && quota_str="${quota_str}${DIM}|${RESET}${rl_color}7d:${week_fmt}%${RESET}" || quota_str="${rl_color}7d:${week_fmt}%${RESET}"
fi

# Build: Sonnet 4.6 [M]|[waiting_icon] c:N%/SZ|quota|branch+*↑N
out=""
if [ -n "$model_id" ]; then
  # Tier color: Haiku=GREEN, Sonnet=CYAN, Opus=MAGENTA
  case "$model_tier" in
    Haiku)  tier_color="$GREEN"   ;;
    Sonnet) tier_color="$CYAN"    ;;
    Opus)   tier_color="$MAGENTA" ;;
    *)      tier_color="$CYAN"    ;;
  esac
  tier_label="${model_tier:-${model_id}}"
  [ -n "$model_version" ] && tier_label="${tier_label} ${model_version}"
  if [ -n "$effort" ]; then
    case "$effort" in
      low)    effort_letter="l"  ;;
      medium) effort_letter="m"  ;;
      high)   effort_letter="h"  ;;
      xhigh)  effort_letter="xh" ;;
      max)    effort_letter="mx" ;;
      *)      effort_letter="$effort" ;;
    esac
    out="${tier_color}${tier_label}${RESET} ${YELLOW}[${effort_letter}]${RESET}"
  else
    out="${tier_color}${tier_label}${RESET}"
  fi
  out="${out}${DIM}|${RESET}"
fi
out="${out}${waiting_icon}"
if [ -n "$ctx_size_fmt" ]; then
  out="${out}${WHITE}c:${ctx_pct}%/${ctx_size_fmt}${RESET}"
else
  out="${out}${WHITE}c:${ctx_pct}%${RESET}"
fi
[ -n "$quota_str" ] && out="${out}${DIM}|${RESET}${quota_str}"
if [ -n "$branch" ]; then
  flags_str=""
  [ -n "$git_flags" ] && flags_str="${YELLOW}${git_flags}${RESET}"
  folder=$(basename "$dir")
  branch_sym=$(printf '\ue0a0')
  out="${out}${DIM}|${RESET}${WHITE}${folder}${RESET} ${BLUE}${branch_sym} ${branch}${RESET}${flags_str}"
fi
printf "%s" "$out"