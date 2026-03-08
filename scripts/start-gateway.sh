#!/usr/bin/env bash
# Start OpenClaw gateway på Linux (VPS). Kør fra openclaw-roden eller med OPENCLAW_ROOT.
# Bruger: chmod +x scripts/start-gateway.sh && ./scripts/start-gateway.sh

set -e
OPENCLAW_ROOT="${OPENCLAW_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$OPENCLAW_ROOT"

# Miljøvariabler (overskriv evt. med .env eller export før kørsel)
export OPENCLAW_GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18789}"
export OPENCLAW_GATEWAY_TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"
# Valgfrit: sæt i ~/.openclaw-gateway-env eller .env i openclaw-roden
if [ -f "$OPENCLAW_ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$OPENCLAW_ROOT/.env"
  set +a
fi
if [ -f "$HOME/.openclaw-gateway-env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$HOME/.openclaw-gateway-env"
  set +a
fi

[ -n "$OPENCLAW_GATEWAY_TOKEN" ] || { echo "OPENCLAW_GATEWAY_TOKEN ikke sat. Sæt i .env eller export."; exit 1; }
export BRAVE_API_KEY="${BRAVE_API_KEY:-}"
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-ollama-local}"

# OpenClaw config skal ligge i $HOME/.openclaw eller i OPENCLAW_ROOT
if [ -f "$OPENCLAW_ROOT/openclaw.json" ]; then
  export OPENCLAW_CONFIG_DIR="$OPENCLAW_ROOT"
elif [ -f "$HOME/.openclaw/openclaw.json" ]; then
  export OPENCLAW_CONFIG_DIR="$HOME/.openclaw"
fi

exec openclaw gateway --port "${OPENCLAW_GATEWAY_PORT}"
