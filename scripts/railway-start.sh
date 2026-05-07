#!/usr/bin/env bash
# Railway start: build openclaw.json from template + env, then start gateway.
# Kør fra repo root (Railway working directory). Kræver: OPENCLAW_GATEWAY_TOKEN, PORT.

set -euo pipefail
ROOT="${OPENCLAW_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

# Brug lokal binary direkte — npx kan ikke genfindes ved OpenClaw's interne respawn i Railway
OPENCLAW="$ROOT/node_modules/.bin/openclaw"

echo "[DEBUG] ROOT=$ROOT PWD=$(pwd)"

# Port fra Railway (påkrævet)
PORT="${PORT:-18789}"
export OPENCLAW_GATEWAY_PORT="$PORT"
echo "[DEBUG] PORT=$PORT"

# Påkrævet token
[ -n "${OPENCLAW_GATEWAY_TOKEN}" ] || { echo "[FATAL] OPENCLAW_GATEWAY_TOKEN ikke sat. Sæt den i Railway Variables."; exit 1; }
echo "[DEBUG] OPENCLAW_GATEWAY_TOKEN is set"

# Default for Telegram allowFrom hvis ikke sat (bruges ikke til override — se build-config.js)
export TELEGRAM_GROUP_ALLOW_FROM="${TELEGRAM_GROUP_ALLOW_FROM:-[]}"

# Byg openclaw.json fra template ved at substituere ${VAR} fra env
# Bruger Node så vi ikke afhænger af envsubst (gettext).
if [ -f "$ROOT/openclaw.railway.example.json" ]; then
  node "$ROOT/scripts/build-config.js" "$ROOT"
  echo "[DEBUG] openclaw.json genereret fra template."
else
  echo "[FATAL] openclaw.railway.example.json ikke fundet!"; exit 1
fi

# Opret workspace og cron så gatewayen ikke fejler
mkdir -p "$ROOT/workspace" "$ROOT/cron"
# Opret tom MEMORY.md så memory_get ikke fejler ved første kald
[ -f "$ROOT/workspace/MEMORY.md" ] || touch "$ROOT/workspace/MEMORY.md"
echo "[DEBUG] workspace + cron dirs OK"

# Kopier config til HOME/.openclaw/ (OpenClaw læser herfra)
REAL_HOME="${HOME:-/root}"
mkdir -p "$REAL_HOME/.openclaw" "$REAL_HOME/.openclaw/agents/main/sessions" "$REAL_HOME/.openclaw/credentials"
cp "$ROOT/openclaw.json" "$REAL_HOME/.openclaw/openclaw.json"
chmod 700 "$REAL_HOME/.openclaw" 2>/dev/null || true
chmod 600 "$REAL_HOME/.openclaw/openclaw.json" 2>/dev/null || true
echo "[DEBUG] Config copied to $REAL_HOME/.openclaw/openclaw.json"

# Kopier også til OPENCLAW_STATE_DIR (volume) hvis det findes
STATE_DIR="${OPENCLAW_STATE_DIR:-/data/.openclaw}"
if [ -d "$STATE_DIR" ]; then
  cp "$ROOT/openclaw.json" "$STATE_DIR/openclaw.json"
  echo "[DEBUG] Config copied to $STATE_DIR/openclaw.json (state dir)"
fi

# === CONFIG VERIFIKATION ===
echo "[DEBUG] openclaw version: $(npm list openclaw --depth=0 2>&1 | grep openclaw || echo 'not found')"
echo "[DEBUG] Config model.primary: $(node -e "try{const c=require('$ROOT/openclaw.json');console.log(c.agents&&c.agents.defaults&&c.agents.defaults.model&&c.agents.defaults.model.primary||'NOT SET')}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] Config telegram.allowFrom: $(node -e "try{const c=require('$ROOT/openclaw.json');const a=c.channels&&c.channels.telegram&&c.channels.telegram.allowFrom;console.log(JSON.stringify(a))}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] Config telegram.botToken sat: $(node -e "try{const c=require('$ROOT/openclaw.json');const t=c.channels&&c.channels.telegram&&c.channels.telegram.botToken;console.log(t&&t.length>0?'JA (len='+t.length+')':'TOM — TELEGRAM VIRKER IKKE')}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] Config gateway.auth.token sat: $(node -e "try{const c=require('$ROOT/openclaw.json');const t=c.gateway&&c.gateway.auth&&c.gateway.auth.token;console.log(t&&t.length>0?'JA':'TOM')}catch(e){console.log('PARSE ERROR:'+e.message)}" 2>&1)"
echo "[DEBUG] GROQ_API_KEY: $([ -n "${GROQ_API_KEY:-}" ] && echo 'sat (len='${#GROQ_API_KEY}')' || echo 'IKKE SAT — 401 ved inference')"
echo "[DEBUG] TELEGRAM_BOT_TOKEN: $([ -n "${TELEGRAM_BOT_TOKEN:-}" ] && echo 'sat' || echo 'IKKE SAT')"
# === SLUT CONFIG VERIFIKATION ===

# Deaktiver OpenClaw CLI respawn (crasher i Railway containers)
export OPENCLAW_NO_RESPAWN=1

# Øg Node heap; vis stack trace ved unhandled rejections
[ -n "${NODE_OPTIONS:-}" ] || export NODE_OPTIONS="--max-old-space-size=1024"
export NODE_OPTIONS="${NODE_OPTIONS} --unhandled-rejections=warn"

# Ryd Telegram webhook + polling-state så vi undgår 409 Conflict.
# deleteWebhook sikrer at ingen webhook er registreret (vi bruger polling).
# getUpdates med timeout=0 tvinger eventuelle gamle polling-sessioner til at stoppe.
echo "[DEBUG] Rydder Telegram webhook og polling-state..."
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" \
  > /dev/null 2>&1 || true
sleep 1
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates?limit=1&timeout=0&offset=-1" \
  > /dev/null 2>&1 || true
sleep 2
echo "[DEBUG] Telegram reset done — klar til polling"

# Verificer openclaw CLI er tilgængeligt
"$OPENCLAW" --version 2>&1 || { echo "[FATAL] openclaw CLI ikke fundet"; exit 1; }

# Send Telegram-notifikation om opstart (baggrundsprocess, fejler stilet)
(sleep 20 && curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=8572521981" \
  --data-urlencode "text=Clawrunner online. Model: groq/llama-3.3-70b-versatile" \
  > /dev/null 2>&1) &

# Watchdog: genstarter gatewayen automatisk ved exit
RESTART_COUNT=0
MAX_RESTARTS=20

run_gateway() {
  echo "[DEBUG] Starter OpenClaw gateway på port $PORT (forsøg $((RESTART_COUNT+1)))..."
  set +e
  "$OPENCLAW" gateway run --port "$PORT" --allow-unconfigured --verbose 2>&1
  EXIT=$?
  set -e
  echo "[EXIT] Gateway stoppede med kode $EXIT"
}

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
  run_gateway
  RESTART_COUNT=$((RESTART_COUNT+1))
  if [ $RESTART_COUNT -lt $MAX_RESTARTS ]; then
    echo "[WATCHDOG] Gateway stoppede. Genstarter om 5s... (forsøg $RESTART_COUNT/$MAX_RESTARTS)"
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=8572521981" \
      --data-urlencode "text=Clawrunner genstartet (forsøg $RESTART_COUNT/$MAX_RESTARTS)" \
      > /dev/null 2>&1 || true
    # Ryd Telegram-state inden genstart så 409 undgås
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" \
      > /dev/null 2>&1 || true
    sleep 5
  fi
done

echo "[WATCHDOG] Max genstarter nået ($MAX_RESTARTS). Afslutter."
exit 1
