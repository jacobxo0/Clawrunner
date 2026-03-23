#!/usr/bin/env bash
# Railway start: build openclaw.json from template + env, then start gateway.
# Kør fra repo root (Railway working directory). Kræver: OPENCLAW_GATEWAY_TOKEN, PORT.

set -euo pipefail
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

# Kopier vores config til HOME/.openclaw/
REAL_HOME="${HOME:-/root}"
mkdir -p "$REAL_HOME/.openclaw" "$REAL_HOME/.openclaw/agents/main/sessions" "$REAL_HOME/.openclaw/credentials"
cp "$ROOT/openclaw.json" "$REAL_HOME/.openclaw/openclaw.json"
chmod 700 "$REAL_HOME/.openclaw" 2>/dev/null || true
chmod 600 "$REAL_HOME/.openclaw/openclaw.json" 2>/dev/null || true
echo "[DEBUG] Config copied to $REAL_HOME/.openclaw/openclaw.json"

# Kopier også til OPENCLAW_STATE_DIR (volume) — OpenClaw læser config herfra.
# Dette sker FØR doctor kører så doctor altid læser den nye config.
STATE_DIR="${OPENCLAW_STATE_DIR:-/data/.openclaw}"
if [ -d "$STATE_DIR" ]; then
  cp "$ROOT/openclaw.json" "$STATE_DIR/openclaw.json"
  echo "[DEBUG] Config copied to $STATE_DIR/openclaw.json (state dir)"
fi

# === CONFIG VERIFICATION (idempotent — altid fra $ROOT/openclaw.json) ===
echo "[DEBUG] openclaw npm version: $(npm list openclaw --depth=0 2>&1 | grep openclaw || echo 'not found')"
echo "[DEBUG] Config model.primary: $(node -e "try{const c=require('$ROOT/openclaw.json');console.log(c.agents&&c.agents.defaults&&c.agents.defaults.model&&c.agents.defaults.model.primary||'NOT SET')}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] GROQ_API_KEY env (LiteLLM auto-reads): $([ -n "${GROQ_API_KEY:-}" ] && echo 'set (len='${#GROQ_API_KEY}')' || echo 'NOT SET — 401 will occur at inference')"
echo "[DEBUG] Config telegram.allowFrom: $(node -e "try{const c=require('$ROOT/openclaw.json');const a=c.channels&&c.channels.telegram&&c.channels.telegram.allowFrom;console.log(JSON.stringify(a))}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] Config telegram.botToken set: $(node -e "try{const c=require('$ROOT/openclaw.json');const t=c.channels&&c.channels.telegram&&c.channels.telegram.botToken;console.log(t&&t.length>0?'YES (len='+t.length+')':'EMPTY')}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] Config gateway.auth.token set: $(node -e "try{const c=require('$ROOT/openclaw.json');const t=c.gateway&&c.gateway.auth&&c.gateway.auth.token;console.log(t&&t.length>0?'YES':'EMPTY')}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] Config brave.apiKey set: $(node -e "try{const c=require('$ROOT/openclaw.json');const t=c.tools&&c.tools.web&&c.tools.web.search&&c.tools.web.search.apiKey;console.log(t&&t.length>0?'YES':'EMPTY')}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
# === END CONFIG VERIFICATION ===

echo "[DEBUG] GROQ_API_KEY is $([ -n "${GROQ_API_KEY:-}" ] && echo 'set' || echo 'NOT SET')"
echo "[DEBUG] TELEGRAM_BOT_TOKEN is $([ -n "${TELEGRAM_BOT_TOKEN:-}" ] && echo 'set' || echo 'NOT SET')"
echo "[DEBUG] BRAVE_API_KEY is $([ -n "${BRAVE_API_KEY:-}" ] && echo 'set' || echo 'NOT SET')"

# Øg Node heap; vis stack trace ved exit og unhandled rejections
[ -n "${NODE_OPTIONS:-}" ] || export NODE_OPTIONS="--max-old-space-size=1024"
export NODE_OPTIONS="${NODE_OPTIONS} --unhandled-rejections=warn --trace-exit"

# Tjek at openclaw findes
echo "[DEBUG] Checking openclaw..."
npx openclaw --version 2>&1 || true
echo "[DEBUG] openclaw check done"

# Kør openclaw doctor (config er allerede kopieret til alle steder ovenfor)
echo "[DEBUG] Running openclaw doctor..."
set +e
NO_COLOR=1 FORCE_COLOR=0 npx openclaw doctor 2>&1
DOCTOR_EXIT=$?
set -e
echo "[DEBUG] Doctor exit: $DOCTOR_EXIT"

# Send Telegram notifikation når gateway starter
(sleep 15 && curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=8572521981" \
  --data-urlencode "text=✅ Clawrunner er online og klar. Model: ollama/llama3.2 (Hetzner)" \
  > /dev/null) &

# Kør gateway
echo "[DEBUG] Starting OpenClaw gateway on port $PORT ..."
set +e
npx openclaw gateway run --port "$PORT" --dev --allow-unconfigured --verbose 2>&1
EXIT=$?
echo "[EXIT] Gateway exited with code $EXIT"
exit $EXIT
