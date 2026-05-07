#!/usr/bin/env bash
# Railway production start — builds openclaw.json from env, starts gateway.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENCLAW="$ROOT/node_modules/.bin/openclaw"

# === STARTUP DIAGNOSTICS ===
echo "=== Railway startup ==="
echo "ROOT:    $ROOT"
echo "PWD:     $(pwd)"
echo "NODE:    $(node --version 2>/dev/null || echo 'NOT FOUND')"
echo "NPM:     $(npm --version 2>/dev/null || echo 'NOT FOUND')"
echo "PATH:    $PATH"
echo "OPENCLAW_BIN: $OPENCLAW"

if [ ! -x "$OPENCLAW" ]; then
  echo "[FATAL] Binary ikke fundet eller ikke eksekverbar: $OPENCLAW"
  echo "Indhold af node_modules/.bin (openclaw*):"
  ls -la "$ROOT/node_modules/.bin/openclaw"* 2>/dev/null || echo "(ingen openclaw-filer fundet)"
  exit 1
fi

echo "OPENCLAW VERSION: $("$OPENCLAW" --version 2>&1 || echo 'version check fejlede')"
echo "=== Startup diagnostics done ==="

# === ENV VALIDATION ===
: "${OPENCLAW_GATEWAY_TOKEN:?[FATAL] OPENCLAW_GATEWAY_TOKEN er ikke sat}"
: "${TELEGRAM_BOT_TOKEN:?[FATAL] TELEGRAM_BOT_TOKEN er ikke sat}"

export PORT="${PORT:-18789}"
export OPENCLAW_GATEWAY_PORT="$PORT"
export OPENCLAW_NO_RESPAWN=1
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1024} --unhandled-rejections=warn"

echo "[DEBUG] ANTHROPIC_API_KEY: $([ -n "${ANTHROPIC_API_KEY:-}" ] && echo "sat (len=${#ANTHROPIC_API_KEY})" || echo 'IKKE SAT')"
echo "[DEBUG] GROQ_API_KEY:      $([ -n "${GROQ_API_KEY:-}" ] && echo "sat (len=${#GROQ_API_KEY})" || echo 'IKKE SAT')"
echo "[DEBUG] PORT: $PORT"

# === BUILD CONFIG ===
if [ ! -f "$ROOT/openclaw.railway.example.json" ]; then
  echo "[FATAL] openclaw.railway.example.json ikke fundet"; exit 1
fi
node "$ROOT/scripts/build-config.js" "$ROOT"
echo "[DEBUG] Config bygget: $ROOT/openclaw.json"

# === SETUP DIRS ===
mkdir -p "$ROOT/workspace" "$ROOT/cron"
[ -f "$ROOT/workspace/MEMORY.md" ] || touch "$ROOT/workspace/MEMORY.md"

REAL_HOME="${HOME:-/root}"
mkdir -p "$REAL_HOME/.openclaw/agents/main/sessions" "$REAL_HOME/.openclaw/credentials"
cp "$ROOT/openclaw.json" "$REAL_HOME/.openclaw/openclaw.json"
chmod 700 "$REAL_HOME/.openclaw" 2>/dev/null || true
chmod 600 "$REAL_HOME/.openclaw/openclaw.json" 2>/dev/null || true

# Ryd stale PID og korrupte session-filer
rm -f "$REAL_HOME/.openclaw/gateway.pid" 2>/dev/null || true
rm -f "$REAL_HOME/.openclaw/agents/main/sessions/"*.jsonl 2>/dev/null || true
echo "[DEBUG] PID + session-filer ryddet"

# Kopier til state dir hvis den findes (Railway volume)
STATE_DIR="${OPENCLAW_STATE_DIR:-/data/.openclaw}"
if [ -d "$STATE_DIR" ]; then
  cp "$ROOT/openclaw.json" "$STATE_DIR/openclaw.json"
  echo "[DEBUG] Config kopieret til state dir: $STATE_DIR"
fi

# === TELEGRAM RESET ===
echo "[DEBUG] Rydder Telegram webhook + polling state..."
curl -sf "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" > /dev/null || true
sleep 1
curl -sf "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates?limit=1&timeout=0&offset=-1" > /dev/null || true
sleep 2
echo "[DEBUG] Telegram reset done"

# === START GATEWAY ===
# exec erstatter shell-processen — gateway bliver PID 1, får korrekte signaler (SIGTERM ved Railway stop)
echo "[DEBUG] Starter gateway på port $PORT..."
exec "$OPENCLAW" gateway run --port "$PORT" --allow-unconfigured
