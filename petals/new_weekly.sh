#!/usr/bin/env bash
set -euo pipefail

START_DATE="${1:-}"
if [[ -n "$START_DATE" ]]; then
  base="$START_DATE"
else
  base="$(date +%F)"
fi

# Monday of this week
dow=$(date -d "$base" +%u)               
week_start=$(date -d "$base -$((dow-1)) days" +%F)
week_end=$(date -d "$week_start +4 days" +%F)

iso_week=$(date -d "$week_start" +%V)    
year=$(date -d "$week_start" +%Y)
month=$(date -d "$week_start" +%B)

start_human=$(date -d "$week_start" +"%b %-d, %Y")
end_human=$(date -d "$week_end"   +"%b %-d, %Y")

ROOT="$(git rev-parse --show-toplevel)"
YEAR_DIR="$ROOT/meadows/bloom-$year"
WEEKLY_DIR="$YEAR_DIR/$month/Weekly"
DEST="$WEEKLY_DIR/${month}-W${iso_week}.md"

mkdir -p "$WEEKLY_DIR"

if [[ -f "$DEST" ]]; then
  echo "Weekly already exists: $DEST"
  exit 0
fi

cat > "$DEST" <<MD
# ⋆˚✿˖° Weekly — ${month} W${iso_week}

**Dates:** $start_human → $end_human

## Highlights
- 

## Lessons
- 

## Next Week Seeds
- 

## Days
{{DAYS_BLOCK}}
MD

echo "Created $DEST"
