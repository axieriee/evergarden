#!/usr/bin/env bash
set -euo pipefail

START_DATE="${1:-}"   # optional: YYYY-MM-DD anywhere in the target week
if [[ -n "$START_DATE" ]]; then
  base="$START_DATE"
else
  base="$(date +%F)"
fi

# Monday-of-week + Friday-of-week
dow=$(date -d "$base" +%u)                        # 1..7 (Mon..Sun)
week_start="$(date -d "$base -$((dow-1)) days" +%F)"
week_end="$(date -d "$week_start +4 days" +%F)"   # Friday

iso_week="$(date -d "$week_start" +%V)"
year="$(date -d "$week_start" +%Y)"
month="$(date -d "$week_start" +%B)"

ROOT="$(git rev-parse --show-toplevel)"
YEAR_DIR="$ROOT/meadows/bloom-$year"
WEEKLY_DIR="$YEAR_DIR/$month/Weekly"
DRAFT="$WEEKLY_DIR/${month}-W${iso_week}.md"

if [[ ! -f "$DRAFT" ]]; then
  echo "Weekly draft not found: $DRAFT"
  echo "Tip: run ./petals/new_weekly.sh [YYYY-MM-DD] first."
  exit 1
fi

# Convert week_start/end to epoch for comparisons
ws_epoch=$(date -d "$week_start" +%s)
we_epoch=$(date -d "$week_end" +%s)

# Collect ONLY dailies within this Mon–Fri window, across any month folder
mapfile -t DAILY_FILES < <(
  find "$YEAR_DIR" -type f \( -path "*/Daily/*.md" -o -path "*/Daily/*.txt" \) \
  -printf "%p\n" \
  | sort \
  | awk -v ws="$ws_epoch" -v we="$we_epoch" '
      function to_epoch(s,  cmd, t) {
        # s like YYYY-MM-DD(.md/.txt)
        # strip extension
        sub(/\.(md|txt)$/,"",s)
        # call date -d safely
        cmd = "date -d \"" s "\" +%s"
        cmd | getline t
        close(cmd)
        return t
      }
      {
        # extract basename
        n = split($0, parts, "/")
        f = parts[n]
        # filename must start with YYYY-MM-DD
        if (match(f, /^[0-9]{4}-[0-9]{2}-[0-9]{2}/)) {
          d = substr(f, 1, 10)
          ep = to_epoch(d)
          if (ep >= ws && ep <= we) print $0
        }
      }'
)

# Build the replacement block
TMPBLOCK="$(mktemp)"
{
  echo "### Included Dailies"
  if (( ${#DAILY_FILES[@]} )); then
    for f in "${DAILY_FILES[@]}"; do
      echo "- $(basename "$f")"
    done
  else
    echo "- _No dailies found in ${week_start} → ${week_end}_"
  fi
  echo
  echo "### Notes Preview"
  echo
  for f in "${DAILY_FILES[@]}"; do
    basef="$(basename "$f")"
    echo "#### $basef"
    head -n 12 "$f" || true
    echo
  done
} > "$TMPBLOCK"

# Replace placeholder line cleanly, preserving layout
if grep -q "{{DAYS_BLOCK}}" "$DRAFT"; then
  sed -i "/{{DAYS_BLOCK}}/{
    r $TMPBLOCK
    d
  }" "$DRAFT"
else
  {
    echo
    echo "## Days"
    echo
    cat "$TMPBLOCK"
  } >> "$DRAFT"
fi

rm -f "$TMPBLOCK"
echo "Updated $DRAFT  (week ${week_start} → ${week_end})"
