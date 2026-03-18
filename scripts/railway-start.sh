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

# OpenClaw læser fra ~/.openclaw/openclaw.json – kopier til rigtig HOME (kør som root i Railway)
REAL_HOME="${HOME:-/root}"
mkdir -p "$REAL_HOME/.openclaw" "$REAL_HOME/.openclaw/agents/main/sessions" "$REAL_HOME/.openclaw/credentials"
cp "$ROOT/openclaw.json" "$REAL_HOME/.openclaw/openclaw.json"
chmod 700 "$REAL_HOME/.openclaw" 2>/dev/null || true
chmod 600 "$REAL_HOME/.openclaw/openclaw.json" 2>/dev/null || true
echo "[DEBUG] REAL_HOME=$REAL_HOME config copied to $REAL_HOME/.openclaw/openclaw.json"

# Øg Node heap; vis stack trace ved exit og unhandled rejections
[ -n "$NODE_OPTIONS" ] || export NODE_OPTIONS="--max-old-space-size=1024"
export NODE_OPTIONS="${NODE_OPTIONS} --unhandled-rejections=warn --trace-exit"

# Tjek at openclaw findes
echo "[DEBUG] Checking openclaw..."
npx openclaw --version 2>&1 || true
echo "[DEBUG] openclaw check done"

echo "[DEBUG] Config file location: ${HOME:-/root}/.openclaw/openclaw.json"
echo "[DEBUG] GROQ_API_KEY is $([ -n "$GROQ_API_KEY" ] && echo 'set' || echo 'NOT SET')"
echo "[DEBUG] TELEGRAM_BOT_TOKEN is $([ -n "$TELEGRAM_BOT_TOKEN" ] && echo 'set' || echo 'NOT SET')"
echo "[DEBUG] BRAVE_API_KEY is $([ -n "$BRAVE_API_KEY" ] && echo 'set' || echo 'NOT SET')"

# Kør openclaw doctor
echo "[DEBUG] Running openclaw doctor..."
set +e
NO_COLOR=1 FORCE_COLOR=0 npx openclaw doctor 2>&1
DOCTOR_EXIT=$?
set -e
echo "[DEBUG] Doctor exit: $DOCTOR_EXIT"

# Kør gateway
echo "[DEBUG] Starting OpenClaw gateway on port $PORT ..."
set +e
npx openclaw gateway run --port "$PORT" --bind loopback --allow-unconfigured --verbose 2>&1
EXIT=$?
echo "[EXIT] Gateway exited with code $EXIT"
exit $EXIT
