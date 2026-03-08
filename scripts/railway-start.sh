#!/usr/bin/env bash
# Railway start: build openclaw.json from template + env, then start gateway.
# Kør fra repo root (Railway working directory). Kræver: OPENCLAW_GATEWAY_TOKEN, PORT.

set -e
ROOT="${OPENCLAW_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

# Port fra Railway (påkrævet)
PORT="${PORT:-18789}"
export OPENCLAW_GATEWAY_PORT="$PORT"

# Påkrævet token
[ -n "${OPENCLAW_GATEWAY_TOKEN}" ] || { echo "OPENCLAW_GATEWAY_TOKEN ikke sat. Sæt den i Railway Variables."; exit 1; }

# Default for Telegram allowFrom hvis ikke sat (tom array)
export TELEGRAM_GROUP_ALLOW_FROM="${TELEGRAM_GROUP_ALLOW_FROM:-[]}"

# Byg openclaw.json fra template ved at substituere ${VAR} fra env
# Bruger Node så vi ikke afhænger af envsubst (gettext).
if [ -f "$ROOT/openclaw.railway.example.json" ]; then
  node -e "
    const fs = require('fs');
    let s = fs.readFileSync('openclaw.railway.example.json', 'utf8');
    const env = process.env;
    function repl(_, name) {
      const v = env[name];
      if (name === 'TELEGRAM_GROUP_ALLOW_FROM') return (v !== undefined && v !== '') ? v : '[]';
      return v !== undefined ? v : '';
    }
    s = s.replace(/\$\{([^}]+)\}/g, repl);
    let cfg = JSON.parse(s);
    if (!env.OLLAMA_BASE_URL || env.OLLAMA_BASE_URL === '') {
      delete cfg.models;
      if (cfg.agents && cfg.agents.defaults && cfg.agents.defaults.models)
        delete cfg.agents.defaults.models['ollama/llama3.2:3b'];
    }
    fs.writeFileSync('openclaw.json', JSON.stringify(cfg, null, 2));
  "
  echo "openclaw.json genereret fra template."
else
  echo "Advarsel: openclaw.railway.example.json ikke fundet; forventer eksisterende openclaw.json."
fi

# Opret workspace og cron så gatewayen ikke fejler
mkdir -p "$ROOT/workspace" "$ROOT/cron"

# OpenClaw læser config fra OPENCLAW_CONFIG_DIR eller current dir
export OPENCLAW_CONFIG_DIR="$ROOT"

exec openclaw gateway --port "$PORT"
