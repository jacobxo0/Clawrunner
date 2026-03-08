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
    const telegramAllow = (env.TELEGRAM_GROUP_ALLOW_FROM && env.TELEGRAM_GROUP_ALLOW_FROM !== '') ? env.TELEGRAM_GROUP_ALLOW_FROM : '[]';
    try {
      let arr;
      try {
        const parsed = JSON.parse(telegramAllow);
        arr = Array.isArray(parsed) ? parsed : [parsed];
      } catch (_) {
        arr = [telegramAllow];
      }
      arr = arr.map(function (id) { return String(id); });
      if (cfg.channels && cfg.channels.telegram) {
        cfg.channels.telegram.groupAllowFrom = arr;
        cfg.channels.telegram.allowFrom = arr;
      }
    } catch (_) {}
    if (!env.OLLAMA_BASE_URL || env.OLLAMA_BASE_URL === '') {
      delete cfg.models;
      if (cfg.agents && cfg.agents.defaults && cfg.agents.defaults.models)
        delete cfg.agents.defaults.models['ollama/llama3.2:3b'];
    }
    fs.writeFileSync('openclaw.json', JSON.stringify(cfg, null, 2));
  "
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

# Doctor er diagnostik; kør ikke på hver start – kan blokere/exit i Railway og forhindre gateway-start
# npx openclaw doctor --fix 2>/dev/null || true

# Øg Node heap; vis uafviklede promise-afvisninger så vi ser fejl i logs
[ -n "$NODE_OPTIONS" ] || export NODE_OPTIONS="--max-old-space-size=1024"
export NODE_OPTIONS="${NODE_OPTIONS} --unhandled-rejections=warn"

# Tjek at openclaw findes (output i logs; fejler vi her, næste linje viser det)
echo "[DEBUG] Checking openclaw..."
npx openclaw --version 2>&1 || true
echo "[DEBUG] openclaw check done"

# Kør gateway; fang stderr til fil og vis den efter exit (så Railway viser den reelle fejl)
echo "[DEBUG] Starting OpenClaw gateway on port $PORT ..."
set +e
GW_STDERR="$ROOT/gateway.stderr"
npx openclaw gateway --port "$PORT" --allow-unconfigured 2> "$GW_STDERR"
EXIT=$?
set -e
if [ -s "$GW_STDERR" ]; then
  echo "[STDERR from gateway]"
  cat "$GW_STDERR"
fi
echo "[FATAL] Gateway exited with code $EXIT"
exit $EXIT
