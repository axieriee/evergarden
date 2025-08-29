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

# Helper: extract a block of lines between start & stop predicates
function Get-TableBlock([string[]]$lines, [int]$startIdx){
  $acc = New-Object System.Collections.Generic.List[string]
  for ($i = $startIdx; $i -lt $lines.Count; $i++){
    $line = $lines[$i]
    if ($line -match '^\s*$') { break }           # stop at blank line after table
    if ($line -notmatch '^\|') { break }          # stop when rows no longer start with |
    $acc.Add($line)
  }
  return $acc -join [Environment]::NewLine
}

# Build weekly section with full tables
$weekHeader = "=== Week $weekNum ($($weekStart.ToString('MMM d')) – $($weekEnd.ToString('MMM d, yyyy'))) ==="
$section = New-Object System.Collections.Generic.List[string]
$section.Add($weekHeader)
$section.Add("")

for ($i=0; $i -lt 5; $i++) {
  $d     = $weekStart.AddDays($i)
  $stamp = $d.ToString('yyyy-MM-dd')
  $f     = Join-Path $dailyDir "$stamp.txt"

  if (-not (Test-Path $f)) {
    $section.Add("--- $stamp ---")
    $section.Add("(no daily file)")
    $section.Add("")
    continue
  }

  $lines = Get-Content $f

  # Find table header line
  $tableHeaderIdx = ($lines | Select-String -Pattern '^\|\s*Symbol\s*\|' -SimpleMatch).LineNumber
  if ($tableHeaderIdx) { $tableHeaderIdx-- } # LineNumber is 1-based

  # Grab the table block (header + separator + rows) until blank line
  $tableBlock = ""
  if ($tableHeaderIdx -ge 0) {
    $tableBlock = Get-TableBlock -lines $lines -startIdx $tableHeaderIdx
  }

  # Grab Day PnL / Market Sentiment / Key Lesson lines
  $pnl    = ($lines | Select-String -Pattern '^\s*Day PnL:\s*.*$').Line
  if (-not $pnl) { $pnl = "Day PnL: (fill in)" }

  $sent   = ($lines | Select-String -Pattern '^\s*Market Sentiment:\s*.*$').Line
  if (-not $sent) { $sent = "Market Sentiment: (fill in)" }

  $lesson = ($lines | Select-String -Pattern '^\s*Key Lesson:\s*.*$').Line
  if (-not $lesson) { $lesson = "Key Lesson: (fill in)" }

  # Append one mini-section per day
  $section.Add("--- $stamp ---")
  if ($tableBlock) {
    $section.Add($tableBlock)
  } else {
    $section.Add("(no trade table found)")
  }
  $section.Add($pnl)
  $section.Add($sent)
  $section.Add($lesson)
  $section.Add("")  # blank line between days
}

# Append to weekly file (do not overwrite what you already wrote)
Add-Content -Path $weeklyFile -Value ($section -join [Environment]::NewLine)

Write-Host "Updated $weeklyFile with full daily tables for $($weekStart.ToString('yyyy-MM-dd')) → $($weekEnd.ToString('yyyy-MM-dd'))"
