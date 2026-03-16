#!/usr/bin/env bash
# Kør på VPS (Ubuntu 22.04): installér Ollama, bind til 0.0.0.0, start tjeneste, åbn firewall, pull model.
# Bruges af plan-ollama-paa-vps.md. Kør: bash install-ollama-vps.sh
#
# VIGTIGT: Sætter OLLAMA_HOST=0.0.0.0:11434 via systemd override så Railway/externe kan nå Ollama.
# Standard Linux-installation binder kun til 127.0.0.1 — det virker ikke med Railway-hosted gateway.

set -e

echo "==> Installerer Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# ── Bind Ollama til 0.0.0.0 (KRITISK for Railway/ekstern adgang) ──────────────
echo "==> Konfigurerer Ollama til at lytte på 0.0.0.0:11434 (krævet for Railway-adgang)..."
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_NUM_CTX=16384"
EOF
sudo systemctl daemon-reload

echo "==> Starter og aktiverer Ollama-tjeneste..."
sudo systemctl start ollama
sudo systemctl enable ollama
sleep 3

echo "==> Tjekker at Ollama kører og lytter på 0.0.0.0:11434..."
curl -sSf http://127.0.0.1:11434/api/tags >/dev/null || {
  echo "[FEJL] Ollama svarer ikke. Tjek: sudo systemctl status ollama && sudo journalctl -u ollama -n 50"
  exit 1
}
echo "Ollama svarer OK."

# ── Firewall ──────────────────────────────────────────────────────────────────
echo "==> Firewall (ufw): åbner 22 (SSH) og 11434 (Ollama)..."
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow 22/tcp
  sudo ufw allow 11434/tcp
  sudo ufw --force enable 2>/dev/null || true
  echo ""
  echo "  [SIKKERHED] Overvej at begrænse 11434 til din gateways IP:"
  echo "    sudo ufw delete allow 11434/tcp"
  echo "    sudo ufw allow from <RAILWAY-IP> to any port 11434"
  echo "  Eller brug Tailscale og fjern port 11434 fra offentlig firewall."
else
  echo "ufw ikke fundet – åbn port 22 og 11434 i din cloud-udbyders firewall (Hetzner/DigitalOcean/etc)."
fi

# ── Pull model ────────────────────────────────────────────────────────────────
echo ""
echo "==> Puller llama3.2:3b (tool-capable, ~2 GB, passer på 4 GB RAM VPS)..."
echo "    Alternativt: ollama pull qwen2.5-coder:7b (bedre til kode, kræver 8 GB RAM)"
ollama pull llama3.2:3b

# ── Verification ──────────────────────────────────────────────────────────────
VPS_IP=$(curl -sSf http://ifconfig.me 2>/dev/null || echo "<VPS-IP>")
echo ""
echo "================================================================"
echo "  Ollama kørende på port 11434 bundet til 0.0.0.0"
echo "  VPS public IP: ${VPS_IP}"
echo ""
echo "  Næste trin:"
echo "  1. Railway Variables → sæt:"
echo "       OLLAMA_BASE_URL = http://${VPS_IP}:11434"
echo "       OLLAMA_API_KEY  = ollama-vps"
echo "  2. AI-CORE Variables → sæt:"
echo "       OLLAMA_BASE_URL = http://${VPS_IP}:11434"
echo "       OLLAMA_DEFAULT_MODEL = llama3.2:3b"
echo "  3. Test: curl http://${VPS_IP}:11434/api/tags"
echo "  4. Redeploy Railway (begge services)"
echo "================================================================"
