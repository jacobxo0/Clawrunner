# Start OpenClaw gateway (PowerShell). Kør fra OpenClaw-roden eller med -OpenClawRoot.
param([string]$OpenClawRoot = $PSScriptRoot + "\..")
$env:OPENCLAW_GATEWAY_PORT = "18789"
$env:OPENCLAW_GATEWAY_TOKEN = "6a7efbadfcb6b422e9a490026d15e847d85baa2c0395ba80"
# Brave Search API (web research). Hvis du ikke vil have nøglen i scriptet: sæt BRAVE_API_KEY i system-miljø i stedet.
if (-not $env:BRAVE_API_KEY) { $env:BRAVE_API_KEY = "BSAJjOrUxcyIbyAkI-rQcpbDUIl0Ztg" }
# Ollama (lokale modeller). Sæt OLLAMA_API_KEY så OpenClaw auto-discoverer modeller på http://127.0.0.1:11434. Se notes/ollama-setup.md.
if (-not $env:OLLAMA_API_KEY) { $env:OLLAMA_API_KEY = "ollama-local" }
Set-Location $OpenClawRoot
# 2026.3.1+: bin er openclaw.mjs. Kør via node så det virker uden openclaw i PATH.
$openclawMjs = "C:\Users\Jnkri\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs"
& "C:\Program Files\nodejs\node.exe" $openclawMjs gateway --port 18789
