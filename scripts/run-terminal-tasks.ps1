# OpenClaw: kør alt terminalarbejde (gateway-check, run_cycle, status).
# Agenten kører dette selv — ingen manuelle kommandoer til brugeren.
param([string]$OpenClawRoot = $PSScriptRoot + "\..")

$ErrorActionPreference = "Continue"
Set-Location $OpenClawRoot

$logDir = Join-Path $OpenClawRoot "logs"
$null = New-Item -ItemType Directory -Force -Path $logDir
$date = Get-Date -Format "yyyy-MM-dd"
$logFile = Join-Path $logDir "terminal-tasks-$date.txt"

function Log { param($msg) Add-Content -Path $logFile -Value "[$(Get-Date -Format 'HH:mm:ss')] $msg" }

Log "=== OpenClaw terminal tasks ==="

# 1) Gateway: er port 18789 i brug?
$listening = netstat -ano 2>$null | Select-String "18789.*LISTENING"
if (-not $listening) {
    Log "Gateway not listening; starting gateway in background."
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\start-gateway.ps1`"" -WorkingDirectory $OpenClawRoot -WindowStyle Hidden
    Start-Sleep -Seconds 6
}
$listening2 = netstat -ano 2>$null | Select-String "18789.*LISTENING"
if ($listening2) { Log "Gateway: port 18789 LISTENING." } else { Log "Gateway: port 18789 not listening (start may be in progress)." }

# 2) Signal Forge run_cycle (workspace)
$venvPython = Join-Path $OpenClawRoot ".venv\Scripts\python.exe"
$workspace = Join-Path $OpenClawRoot "workspace"
$runCycle = Join-Path $workspace "scripts\run_cycle.py"
if (Test-Path $venvPython) {
    Log "Running run_cycle.py ..."
    & $venvPython $runCycle 2>&1 | ForEach-Object { Log $_ }
    Log "run_cycle done."
} else {
    Log "Skipped run_cycle (no .venv python)."
}

# 3) Cron status fra jobs.json (læsbar for agent)
$cronPath = Join-Path $OpenClawRoot "cron\jobs.json"
if (Test-Path $cronPath) {
    $jobs = Get-Content $cronPath -Raw | ConvertFrom-Json
    $names = $jobs.jobs | ForEach-Object { $_.name }
    Log "Cron jobs in config: $($names -join ', ')"
}

Log "=== End ==="
Write-Output "Done. Log: $logFile"
