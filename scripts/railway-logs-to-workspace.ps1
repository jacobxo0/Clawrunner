# Hent seneste Railway build- og deploy-logs til workspace, så agenten kan læse dem.
# Kræver: Railway CLI (npm i -g @railway/cli) og railway link eller LOGIN.
# Kør fra OpenClaw-roden: .\scripts\railway-logs-to-workspace.ps1

$OpenClawRoot = if ($PSScriptRoot) { Join-Path $PSScriptRoot ".." } else { "C:\Users\Jnkri\.openclaw" }
$OpenClawRoot = [System.IO.Path]::GetFullPath($OpenClawRoot)
$logDir = Join-Path $OpenClawRoot "logs"
$null = New-Item -ItemType Directory -Force -Path $logDir
$outPath = Join-Path $logDir "railway-latest.txt"

Set-Location $OpenClawRoot
$header = "=== Railway logs @ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===`n"
$header | Set-Content $outPath -Encoding UTF8

# Build logs (fejl vises ofte her)
try {
    railway logs --latest --build --lines 200 2>&1 | Add-Content $outPath -Encoding UTF8
} catch {
    "railway logs --build failed: $_" | Add-Content $outPath -Encoding UTF8
}
"`n--- Deploy/runtime logs ---`n" | Add-Content $outPath -Encoding UTF8
try {
    railway logs --latest --lines 100 2>&1 | Add-Content $outPath -Encoding UTF8
} catch {
    "railway logs failed: $_" | Add-Content $outPath -Encoding UTF8
}

Write-Output "Logs written to $outPath"
