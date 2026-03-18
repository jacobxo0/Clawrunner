#!/usr/bin/env bash
# Railway start: build openclaw.json from template + env, then start gateway.
# Kør fra repo root (Railway working directory). Kræver: OPENCLAW_GATEWAY_TOKEN, PORT.

set -e
ROOT="${OPENCLAW_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

echo "[DEBUG] ROOT=$ROOT PWD=$(pwd)"

# Port fra Railway (påkrævet)
PORT="${PORT:-18789}"
export OPENCLAW_GATEWAY_PORT="$PORT"
echo "[DEBUG] PORT=$PORT"

# Påkrævet token
[ -n "${OPENCLAW_GATEWAY_TOKEN}" ] || { echo "[FATAL] OPENCLAW_GATEWAY_TOKEN ikke sat. Sæt den i Railway Variables."; exit 1; }
echo "[DEBUG] OPENCLAW_GATEWAY_TOKEN is set"

# Default for Telegram allowFrom hvis ikke sat (tom array)
export TELEGRAM_GROUP_ALLOW_FROM="${TELEGRAM_GROUP_ALLOW_FROM:-[]}"

# Byg openclaw.json fra template ved at substituere ${VAR} fra env
# Bruger Node så vi ikke afhænger af envsubst (gettext).
if [ -f "$ROOT/openclaw.railway.example.json" ]; then
  node "$ROOT/scripts/build-config.js" "$ROOT"
  echo "[DEBUG] openclaw.json genereret fra template."
else
  echo "[DEBUG] Advarsel: openclaw.railway.example.json ikke fundet."
fi

# Opret workspace og cron så gatewayen ikke fejler
mkdir -p "$ROOT/workspace" "$ROOT/cron"
echo "[DEBUG] workspace + cron dirs OK"

# OpenClaw læser som standard fra ~/.openclaw/openclaw.json – sæt HOME så den finder vores config
export OPENCLAW_CONFIG_DIR="$ROOT"
mkdir -p "$ROOT/.openclaw" "$ROOT/.openclaw/agents/main/sessions" "$ROOT/.openclaw/credentials"
cp "$ROOT/openclaw.json" "$ROOT/.openclaw/openclaw.json"
chmod 700 "$ROOT/.openclaw" 2>/dev/null || true
chmod 600 "$ROOT/.openclaw/openclaw.json" 2>/dev/null || true
export HOME="$ROOT"
echo "[DEBUG] .openclaw config dir OK OPENCLAW_CONFIG_DIR=$OPENCLAW_CONFIG_DIR"

# Øg Node heap; vis stack trace ved exit og unhandled rejections
[ -n "$NODE_OPTIONS" ] || export NODE_OPTIONS="--max-old-space-size=1024"
export NODE_OPTIONS="${NODE_OPTIONS} --unhandled-rejections=warn --trace-exit"

# Tjek at openclaw findes
echo "[DEBUG] Checking openclaw..."
npx openclaw --version 2>&1 || true
echo "[DEBUG] openclaw check done"

# Dump den genererede config (rediger apikeys ud for sikkerhed)
echo "[DEBUG] Generated openclaw.json (sanitized):"
node -e "
const fs = require('fs');
const cfg = JSON.parse(fs.readFileSync('$ROOT/.openclaw/openclaw.json','utf8'));
if(cfg.tools&&cfg.tools.web&&cfg.tools.web.search) cfg.tools.web.search.apiKey='<redacted>';
if(cfg.gateway&&cfg.gateway.auth) cfg.gateway.auth.token='<redacted>';
if(cfg.channels&&cfg.channels.telegram) cfg.channels.telegram.botToken='<redacted>';
console.log(JSON.stringify(cfg,null,2));
" 2>&1 || true

# Kør openclaw doctor for at se valideringsfejl
echo "[DEBUG] Running openclaw doctor..."
set +e
npx openclaw doctor 2>&1 || true
set -e
echo "[DEBUG] Doctor done"

# Kør gateway
echo "[DEBUG] Starting OpenClaw gateway on port $PORT ..."
set +e
npx openclaw gateway run --port "$PORT" --dev --allow-unconfigured --verbose 2>&1
EXIT=$?
echo "[EXIT] Gateway exited with code $EXIT"
exit $EXIT
