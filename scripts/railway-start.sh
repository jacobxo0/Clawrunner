#!/usr/bin/env bash
# Railway start: build openclaw.json fra template + env, start gateway.

set -euo pipefail
ROOT="${OPENCLAW_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

OPENCLAW="$ROOT/node_modules/.bin/openclaw"

echo "[DEBUG] ROOT=$ROOT PWD=$(pwd)"

PORT="${PORT:-18789}"
export OPENCLAW_GATEWAY_PORT="$PORT"
echo "[DEBUG] PORT=$PORT"

[ -n "${OPENCLAW_GATEWAY_TOKEN}" ] || { echo "[FATAL] OPENCLAW_GATEWAY_TOKEN ikke sat."; exit 1; }

export TELEGRAM_GROUP_ALLOW_FROM="${TELEGRAM_GROUP_ALLOW_FROM:-[]}"

if [ -f "$ROOT/openclaw.railway.example.json" ]; then
  node "$ROOT/scripts/build-config.js" "$ROOT"
  echo "[DEBUG] Config bygget."
else
  echo "[FATAL] openclaw.railway.example.json ikke fundet!"; exit 1
fi

mkdir -p "$ROOT/workspace" "$ROOT/cron"
[ -f "$ROOT/workspace/MEMORY.md" ] || touch "$ROOT/workspace/MEMORY.md"

REAL_HOME="${HOME:-/root}"
mkdir -p "$REAL_HOME/.openclaw" "$REAL_HOME/.openclaw/agents/main/sessions" "$REAL_HOME/.openclaw/credentials"
cp "$ROOT/openclaw.json" "$REAL_HOME/.openclaw/openclaw.json"
chmod 700 "$REAL_HOME/.openclaw" 2>/dev/null || true
chmod 600 "$REAL_HOME/.openclaw/openclaw.json" 2>/dev/null || true
echo "[DEBUG] Config kopieret til $REAL_HOME/.openclaw/openclaw.json"

STATE_DIR="${OPENCLAW_STATE_DIR:-/data/.openclaw}"
if [ -d "$STATE_DIR" ]; then
  cp "$ROOT/openclaw.json" "$STATE_DIR/openclaw.json"
fi

echo "[DEBUG] GROQ_API_KEY: $([ -n "${GROQ_API_KEY:-}" ] && echo 'sat' || echo 'IKKE SAT')"
echo "[DEBUG] TELEGRAM_BOT_TOKEN: $([ -n "${TELEGRAM_BOT_TOKEN:-}" ] && echo 'sat' || echo 'IKKE SAT')"

export OPENCLAW_NO_RESPAWN=1
[ -n "${NODE_OPTIONS:-}" ] || export NODE_OPTIONS="--max-old-space-size=1024"
export NODE_OPTIONS="${NODE_OPTIONS} --unhandled-rejections=warn"

echo "[DEBUG] Rydder Telegram webhook..."
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" > /dev/null 2>&1 || true
sleep 1
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates?limit=1&timeout=0&offset=-1" > /dev/null 2>&1 || true
sleep 2
echo "[DEBUG] Telegram reset done"

"$OPENCLAW" --version 2>&1 || { echo "[FATAL] openclaw CLI ikke fundet"; exit 1; }

RESTART_COUNT=0
MAX_RESTARTS=20

run_gateway() {
  echo "[DEBUG] Starter gateway på port $PORT (forsøg $((RESTART_COUNT+1)))..."
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
    echo "[WATCHDOG] Genstarter om 5s... ($RESTART_COUNT/$MAX_RESTARTS)"
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" > /dev/null 2>&1 || true
    sleep 5
  fi
done

echo "[WATCHDOG] Max genstarter nået. Afslutter."
exit 1
