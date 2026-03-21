# Installer dependencies i 4 batcher (undgå SIGKILL / timeout).
# Kør fra: workspace\projects\nft-arbitrage
# Forudsætning: .venv findes (ellers: python -m venv .venv)

$ErrorActionPreference = "Stop"
$projRoot = $PSScriptRoot
if (-not (Test-Path "$projRoot\.venv\Scripts\Activate.ps1")) {
    Write-Host "Opretter .venv ..."
    Set-Location $projRoot
    python -m venv .venv
}
& "$projRoot\.venv\Scripts\Activate.ps1"
Set-Location $projRoot
python -m pip install --upgrade pip -q

$batches = @(
    "requirements-1-base.txt",
    "requirements-2-web.txt",
    "requirements-3-blockchain-ai.txt",
    "requirements-4-ml-test.txt"
)
$n = 0
foreach ($f in $batches) {
    $n++
    if (-not (Test-Path $f)) { Write-Warning "Skip: $f"; continue }
    Write-Host "`n=== Batch $n/4: $f ===" -ForegroundColor Cyan
    pip install -r $f
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    if ($n -lt $batches.Count) {
        Write-Host "Batch $n færdig. Vent 30 sek (lad systemet falde til ro) før næste ..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
    }
}
Write-Host "`nAlle 4 batcher installeret." -ForegroundColor Green
