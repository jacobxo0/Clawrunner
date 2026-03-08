#!/usr/bin/env bash
# Kør på VPS efter gateway er startet. Verificer at port 18789 lytter og (valgfrit) at processen kører.
set -e
echo "=== OpenClaw gateway check ==="
echo -n "Port 18789: "
if ss -tlnp 2>/dev/null | grep -q 18789 || netstat -tlnp 2>/dev/null | grep -q 18789; then
  echo "LISTENING"
else
  echo "NOT listening - gateway may not be running"
  exit 1
fi
echo -n "Process: "
if pgrep -f "openclaw.*gateway" >/dev/null; then
  echo "running"
else
  echo "not found (might be OK if run via systemd under different name)"
fi
echo "Done. From your PC with SSH tunnel: openclaw cron list"
