#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./petals/new_monthly.sh            # uses today's date
#   ./petals/new_monthly.sh 2025-09-02 # any date in the month you want

BASE_DATE="${1:-$(date +%F)}"  # YYYY-MM-DD

# Month pieces
year="$(date -d "$BASE_DATE" +%Y)"          # e.g., 2025
month="$(date -d "$BASE_DATE" +%B)"         # e.g., September
month_num="$(date -d "$BASE_DATE" +%m)"     # e.g., 09

# Month start/end (for display)
month_start="$(date -d "${year}-${month_num}-01" +%F)"
month_end="$(date -d "${year}-${month_num}-01 +1 month -1 day" +%F)"

start_human="$(date -d "$month_start" +"%b %-d, %Y")"
end_human="$(date -d "$month_end"   +"%b %-d, %Y")"

ROOT="$(git rev-parse --show-toplevel)"
YEAR_DIR="$ROOT/meadows/bloom-$year"
MONTH_DIR="$YEAR_DIR/$month"
DEST="$MONTH_DIR/${month}-${year}.md"

mkdir -p "$MONTH_DIR"

if [[ -f "$DEST" ]]; then
  echo "Monthly already exists: $DEST"
  exit 0
fi

# Look for a template
CANDIDATES=(
  "$ROOT/meadows/patterns/monthly.md"
  "$ROOT/patterns/monthly.md"
)
TEMPLATE=""
for t in "${CANDIDATES[@]}"; do
  [[ -f "$t" ]] && TEMPLATE="$t" && break
done

if [[ -z "$TEMPLATE" ]]; then
  cat > "$DEST" <<MD
# 🌕 Monthly — ${month} ${year}

**Dates Covered:** ${start_human} → ${end_human}

## Highlights 🌼
- 

## Struggles / Weeds 🌿
- 

## Patterns & Themes 🔄
- 

## Seeds for Next Month 🌱
- 

## Overall Reflection ✨
- 
MD
else
  sed -e "s/{{MONTH}}/${month}/g" \
      -e "s/{{YEAR}}/${year}/g" \
      -e "s/{{START_DATE}}/${start_human}/g" \
      -e "s/{{END_DATE}}/${end_human}/g" \
      "$TEMPLATE" > "$DEST"
fi

echo "Created $DEST"
