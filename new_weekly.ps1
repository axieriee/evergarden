param(
  # Pass a Monday as YYYY-MM-DD, or omit to use "this week" Monday
  [string]$Start
)

# Helper: get Monday of the week for a given date (or today)
function Get-WeekStart([datetime]$d){
  # PowerShell DayOfWeek: Sunday=0 ... Saturday=6
  $dow = [int]$d.DayOfWeek
  # We want Monday as start. If Sunday (0), go back 6; else go back (dow-1)
  $back = ($dow - 1)
  if ($back -lt 0) { $back = 6 }
  return $d.AddDays(-$back).Date
}

# Parse input or default to this week's Monday
if ([string]::IsNullOrWhiteSpace($Start)) {
  $weekStart = Get-WeekStart (Get-Date)
} else {
  $weekStart = [datetime]::ParseExact($Start,'yyyy-MM-dd',$null)
}

$weekEnd = $weekStart.AddDays(4)
$year    = $weekStart.Year
$month   = $weekStart.ToString('MMMM')

# ISO-like week number
$culture = [System.Globalization.CultureInfo]::InvariantCulture
$calendar = $culture.Calendar
$weekRule = [System.Globalization.CalendarWeekRule]::FirstFourDayWeek
$firstDay = [System.DayOfWeek]::Monday
$weekNum  = $calendar.GetWeekOfYear($weekStart, $weekRule, $firstDay)

$root      = $PSScriptRoot
$templates = Join-Path $root "Templates"
$tplPath   = Join-Path $templates "02_Weekly_Review_Template.txt"

$monthDir  = Join-Path $root "$year\$month"
$weeklyDir = Join-Path $monthDir "Weekly"
New-Item -ItemType Directory -Force -Path $weeklyDir | Out-Null

$dest = Join-Path $weeklyDir ("Week_{0}-W{1:D2}.txt" -f $year, $weekNum)

# Build replacements
$weekLabel  = ("Week {0}" -f $weekNum)
$startHuman = $weekStart.ToString("MMM d, yyyy")
$endHuman   = $weekEnd.ToString("MMM d, yyyy")

if (-not (Test-Path $tplPath)) { Write-Host "Missing template: $tplPath"; exit 1 }

$content = Get-Content $tplPath -Raw
$content = $content.Replace("{{WEEK_LABEL}}", $weekLabel)
$content = $content.Replace("{{START_DATE}}", $startHuman)
$content = $content.Replace("{{END_DATE}}",   $endHuman)
$content = $content.Replace("{{DAYS_BLOCK}}", "(run weekly_draft.ps1 to fill this)")

Set-Content -Path $dest -Value $content
Write-Host "Created $dest"
