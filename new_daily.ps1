# Creates TradingJournal/YYYY/Month/Daily/YYYY-MM-DD.txt from template
$today = Get-Date
$year  = $today.Year
$month = $today.ToString("MMMM")
$stamp = $today.ToString("yyyy-MM-dd")

$root   = $PSScriptRoot
$monthDir = Join-Path $root "$year\$month"
$dailyDir = Join-Path $monthDir "Daily"
$template = Join-Path $root "Templates\01_Daily_PnL_Table_Template.txt"
$dest     = Join-Path $dailyDir "$stamp.txt"

New-Item -ItemType Directory -Force -Path $dailyDir | Out-Null

if (-not (Test-Path $template)) {
  Write-Host "Template missing at $template"; exit 1
}

(Get-Content $template) -replace "YYYY-MM-DD", $stamp | Set-Content $dest
Write-Host "Created $dest"
