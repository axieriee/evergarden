#!/usr/bin/env bash
set -euo pipefail

# --- Date pieces (matches your PS script) ---
today_stamp="$(date +%F)"      # YYYY-MM-DD
year="$(date +%Y)"             # 2025
month="$(date +%B)"            # e.g., September

# --- Repo paths ---
ROOT="$(git rev-parse --show-toplevel)"

# Year folder as a "bloom"
YEAR_DIR="$ROOT/meadows/bloom-$year"
DAILY_DIR="$YEAR_DIR/$month/Daily"
DEST="$DAILY_DIR/$today_stamp.txt"

# --- Template search (pick the first that exists) ---
CANDIDATES=(
  "$ROOT/meadows/patterns/daily.md"
  "$ROOT/meadows/patterns/01_Daily_PnL_Table_Template.txt"
  "$ROOT/patterns/daily.md"
  "$ROOT/patterns/01_Daily_PnL_Table_Template.txt"
)

TEMPLATE=""
for t in "${CANDIDATES[@]}"; do
  if [[ -f "$t" ]]; then
    TEMPLATE="$t"
    break
  fi
done

# --- Ensure target dir exists ---
mkdir -p "$DAILY_DIR"

# --- Make the file ---
if [[ -z "$TEMPLATE" ]]; then
  # No template found: create a friendly default
  cat > "$DEST" <<EOF
# 🌸 Daily — $today_stamp

## Plan
- 

## Trades
- 

## Reflection
- 
EOF
else
  # Use template and replace either placeholder style
  # Supports {{DATE}} or YYYY-MM-DD token
  sed -e "s/{{DATE}}/$today_stamp/g" \
      -e "s/YYYY-MM-DD/$today_stamp/g" \
      "$TEMPLATE" > "$DEST"
fi

echo "Created $DEST"
