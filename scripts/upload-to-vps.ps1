# Upload OpenClaw til VPS (fra Windows). Kør fra OpenClaw-roden.
# Brug: .\scripts\upload-to-vps.ps1 -VpsIp "DIN_VPS_IP" -VpsUser "ubuntu"
# Valgfrit: -WorkspacePath "/home/ubuntu/openclaw/workspace" (default er /home/<VpsUser>/openclaw/workspace)

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsIp,
    [string]$VpsUser = "ubuntu",
    [string]$LinuxWorkspacePath = ""
)

$ErrorActionPreference = "Stop"
$OpenClawRoot = if ($PSScriptRoot) { Join-Path $PSScriptRoot ".." } else { "C:\Users\Jnkri\.openclaw" }
$OpenClawRoot = [System.IO.Path]::GetFullPath($OpenClawRoot)
Set-Location $OpenClawRoot

if (-not $LinuxWorkspacePath) {
    $LinuxWorkspacePath = "/home/$VpsUser/openclaw/workspace"
}

$dest = "${VpsUser}@${VpsIp}:~/openclaw"

Write-Host "OpenClaw root: $OpenClawRoot"
Write-Host "Destination: $dest"
Write-Host "Workspace path on VPS: $LinuxWorkspacePath"
Write-Host ""

# Lav midlertidig openclaw.json med Linux workspace-sti (tekst-erstatning)
$jsonPath = Join-Path $OpenClawRoot "openclaw.json"
$content = Get-Content $jsonPath -Raw -Encoding UTF8
# Erstat Windows workspace-sti med Linux-sti (uanset hvordan den står i filen)
$content = $content -replace '"workspace":\s*"[^"]*"', "`"workspace`": `"$LinuxWorkspacePath`""
$tempJson = Join-Path $env:TEMP "openclaw-cloud.json"
Set-Content $tempJson -Value $content -Encoding UTF8 -NoNewline

Write-Host "1/4 Uploading openclaw.json (with Linux workspace path)..."
scp $tempJson "${dest}/openclaw.json"
Remove-Item $tempJson -ErrorAction SilentlyContinue

Write-Host "2/4 Uploading cron/jobs.json..."
scp (Join-Path $OpenClawRoot "cron\jobs.json") "${dest}/cron/"

Write-Host "3/4 Uploading scripts..."
$scriptFiles = @(
  (Join-Path $OpenClawRoot "scripts\start-gateway.sh"),
  (Join-Path $OpenClawRoot "scripts\.env.cloud.example"),
  (Join-Path $OpenClawRoot "scripts\openclaw-gateway.service"),
  (Join-Path $OpenClawRoot "scripts\verify-gateway-vps.sh")
)
scp $scriptFiles "${dest}/scripts/"

Write-Host "4/4 Uploading workspace (this can take a while)..."
$ws = Join-Path $OpenClawRoot "workspace"
if (-not (Test-Path $ws)) { Write-Warning "Workspace not found: $ws"; exit 1 }
scp -r "$ws\*" "${dest}/workspace/"

Write-Host ""
Write-Host "Done. Next on VPS:"
Write-Host "  cd ~/openclaw && cp scripts/.env.cloud.example .env && nano .env   # set OPENCLAW_GATEWAY_TOKEN, BRAVE_API_KEY"
Write-Host "  chmod +x scripts/start-gateway.sh"
Write-Host "  # If using ~/.openclaw for config: mkdir -p ~/.openclaw && cp openclaw.json ~/.openclaw/"
Write-Host "  ./scripts/start-gateway.sh   # test run, or install systemd and start service"
Write-Host "  See: notes/cloud-deployment-runbook.md"
