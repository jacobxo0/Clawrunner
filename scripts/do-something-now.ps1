# Gør én konkret ting: skriv til OPENCLAW-RAN.txt så du ser at noget kørte.
$root = Split-Path $PSScriptRoot -Parent
$outFile = Join-Path $root "OPENCLAW-RAN.txt"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$buildLog = Join-Path $root "workspace\projects\instant-mesh\logs\build-log.md"
$line = "Sidst kørt: $ts"
$next = "Tjek build-log: $buildLog"
Set-Content -Path $outFile -Value @($line, $next) -Encoding UTF8
Write-Host "Skrevet til $outFile"
