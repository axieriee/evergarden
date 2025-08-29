param(
  # Monday date for the week, e.g. 2025-08-25. If omitted, uses this week's Monday.
  [string]$Start
)

function Get-WeekStart([datetime]$d){
  $dow = [int]$d.DayOfWeek
  $back = ($dow - 1)
  if ($back -lt 0) { $back = 6 }
  return $d.AddDays(-$back).Date
}

# Resolve week start
if ([string]::IsNullOrWhiteSpace($Start)) {
  $weekStart = Get-WeekStart (Get-Date)
} else {
  $weekStart = [datetime]::ParseExact($Start,'yyyy-MM-dd',$null)
}
$weekEnd = $weekStart.AddDays(4)

$year     = $weekStart.Year
$month    = $weekStart.ToString('MMMM')

$culture  = [System.Globalization.CultureInfo]::InvariantCulture
$calendar = $culture.Calendar
$weekRule = [System.Globalization.CalendarWeekRule]::FirstFourDayWeek
$firstDay = [System.DayOfWeek]::Monday
$weekNum  = $calendar.GetWeekOfYear($weekStart, $weekRule, $firstDay)

$root       = $PSScriptRoot
$monthDir   = Join-Path $root "$year\$month"
$dailyDir   = Join-Path $monthDir "Daily"
$weeklyDir  = Join-Path $monthDir "Weekly"
$weeklyFile = Join-Path $weeklyDir ("Week_{0}-W{1:D2}.txt" -f $year, $weekNum)

if (-not (Test-Path $dailyDir))  { Write-Host "Missing Daily folder: $dailyDir";  exit 1 }
if (-not (Test-Path $weeklyFile)){ Write-Host "Missing weekly file. Run .\new_weekly.ps1 first."; exit 1 }

# Helpers
function Get-TableBlock([string[]]$lines, [int]$startIdx){
  $acc = New-Object System.Collections.Generic.List[string]
  for ($i = $startIdx; $i -lt $lines.Count; $i++){
    $line = $lines[$i]
    if ($line -match '^\s*$') { break }      # stop at blank line
    if ($line -notmatch '^\s*\|') { break }  # stop if not a table row
    $acc.Add($line)
  }
  return $acc -join [Environment]::NewLine
}

function Split-Cells([string]$row){
  # returns trimmed cell array from a pipe row
  $cells = ($row -split '\|') | ForEach-Object { $_.Trim() }
  if ($cells.Count -ge 2) { return $cells[1..($cells.Count-2)] }
  return @()
}

function Convert-ToNumber([string]$s){
  if (-not $s) { return $null }
  $t = $s -replace '[\s,$+]',''  # drop spaces, commas, $, +
  if ($t -match '^-?\d+(\.\d+)?$'){ return [double]$t }
  return $null
}

# Build detailed per-day block (NO "Days:" header)
$detail = New-Object System.Collections.Generic.List[string]

# Weekly stats
$totalTrades = 0
$wins = 0
$losses = 0
$netPnL = 0.0

for ($i=0; $i -lt 5; $i++) {
  $d     = $weekStart.AddDays($i)
  $stamp = $d.ToString('yyyy-MM-dd')
  $f     = Join-Path $dailyDir "$stamp.txt"

  $detail.Add("--- $stamp ---")
  if (-not (Test-Path $f)) {
    $detail.Add("(no daily file)")
    $detail.Add("")
    continue
  }

  $lines = Get-Content $f

  # Find header row (allow "Symbol" or "Ticker")
  $hdrMatch = ($lines | Select-String -Pattern '^\s*\|\s*(Symbol|Ticker)\s*\|' -CaseSensitive:$false | Select-Object -First 1)
  $tableHeaderIdx = -1
  if ($hdrMatch) { $tableHeaderIdx = $hdrMatch.LineNumber - 1 }  # 1-based to 0-based

  $pnlColIndex = $null

  if ($tableHeaderIdx -ge 0) {
    # Grab table block to paste
    $tableBlock = Get-TableBlock -lines $lines -startIdx $tableHeaderIdx
    if ($tableBlock) { $detail.Add($tableBlock) } else { $detail.Add("(no trade table found)") }

    # Determine PnL column index from header cells for stats
    $headerCells = Split-Cells $lines[$tableHeaderIdx]
    for ($c=0; $c -lt $headerCells.Count; $c++){
      if ($headerCells[$c] -match '^\s*PnL\s*$'){ $pnlColIndex = $c; break }
    }

    # Walk data rows (skip header + separator line)
    for ($r = $tableHeaderIdx + 2; $r -lt $lines.Count; $r++){
      $row = $lines[$r]
      if ($row -match '^\s*$') { break }
      if ($row -notmatch '^\s*\|') { break }
      $cells = Split-Cells $row
      if ($cells.Count -eq 0) { break }

      $pnlStr = $null
      if ($null -ne $pnlColIndex -and $pnlColIndex -lt $cells.Count){
        $pnlStr = $cells[$pnlColIndex]
      } elseif ($cells.Count -ge 2) {
        # fallback: second-to-last cell
        $pnlStr = $cells[$cells.Count-2]
      }

      $pnl = Parse-Number $pnlStr
      if ($null -ne $pnl){
        $totalTrades++
        $netPnL += $pnl
        if ($pnl -gt 0) { $wins++ }
        elseif ($pnl -lt 0) { $losses++ }
      }
    }
  } else {
    $detail.Add("(no trade table found)")
  }

  # Summary lines from daily
  $pnlLine = ($lines | Select-String -Pattern '^\s*Day PnL:\s*.*$' | Select-Object -First 1).Line
  if (-not $pnlLine) { $pnlLine = "Day PnL: (fill in)" }

  $sentLine = ($lines | Select-String -Pattern '^\s*Market Sentiment:\s*.*$' | Select-Object -First 1).Line
  if (-not $sentLine) { $sentLine = "Market Sentiment: (fill in)" }

  $lessonLine = ($lines | Select-String -Pattern '^\s*Key Lesson:\s*.*$' | Select-Object -First 1).Line
  if (-not $lessonLine) { $lessonLine = "Key Lesson: (fill in)" }

  $detail.Add($pnlLine)
  $detail.Add($sentLine)
  $detail.Add($lessonLine)
  $detail.Add("")  # blank line between days
}

$newBlock = ($detail -join [Environment]::NewLine)

# Read weekly file
$contents = Get-Content $weeklyFile -Raw

# Replace {{DAYS_BLOCK}} or hint text if present (NO "Days:" label)
if ($contents -match [regex]::Escape("{{DAYS_BLOCK}}")) {
  $contents = $contents.Replace("{{DAYS_BLOCK}}", $newBlock)
  Write-Host "Replaced {{DAYS_BLOCK}}"
} elseif ($contents -match [regex]::Escape("(run weekly_draft.ps1 to fill this)")) {
  $contents = $contents.Replace("(run weekly_draft.ps1 to fill this)", $newBlock)
  Write-Host "Replaced hint text"
} else {
  # If neither placeholder is present, append at end
  $contents = $contents + [Environment]::NewLine + $newBlock
  Write-Host "Appended detailed block at end"
}

# Compute win%
$winPct = if ($totalTrades -gt 0) { [math]::Round(($wins / $totalTrades) * 100, 2) } else { 0 }

# Replace the Stats block in the weekly file (from "Stats:" until next blank line)
$statsBlock = @(
  "Stats:",
  "- Total Trades: $totalTrades",
  "- Win%: $winPct%",
  "- Net PnL: $netPnL"
) -join [Environment]::NewLine

$contents = [regex]::Replace($contents, "Stats:[\s\S]*?(?=\r?\n\r?\n|$)", $statsBlock)

# Save
Set-Content -Path $weeklyFile -Value $contents -Encoding UTF8

Write-Host ("Updated {0} with details and stats for {1} -> {2}" -f $weeklyFile, $weekStart.ToString('yyyy-MM-dd'), $weekEnd.ToString('yyyy-MM-dd'))
