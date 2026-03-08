#!/usr/bin/env bash
# Kør på VPS (Ubuntu 22.04): installér Ollama, start tjeneste, åbn firewall, pull et lille model.
# Bruges af plan-ollama-paa-vps.md. Kør: curl -sSL <raw-url> | bash  eller  bash install-ollama-vps.sh

set -e

echo "==> Installerer Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "==> Starter og aktiverer Ollama-tjeneste..."
sudo systemctl start ollama 2>/dev/null || true
sudo systemctl enable ollama 2>/dev/null || true
sleep 2

echo "==> Tjekker at Ollama kører på 11434..."
curl -sSf http://127.0.0.1:11434/api/tags >/dev/null || { echo "Advarsel: Ollama svarer ikke endnu. Prøv: sudo systemctl restart ollama"; exit 1; }

echo "==> Firewall (ufw): åbner 22 og 11434..."
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow 22/tcp
  sudo ufw allow 11434/tcp
  echo "Bemærk: Begræns 11434 til Railway/IP hvis ønsket: sudo ufw allow from <IP> to any port 11434 && sudo ufw deny 11434"
  sudo ufw --force enable 2>/dev/null || true
else
  echo "ufw ikke fundet – sørg for at åbne 22 og 11434 i din cloud firewall."
fi

echo "==> Puller model llama3.2:3b (kan tage et par minutter)..."
ollama pull llama3.2:3b

echo "==> Ferdig. Ollama kører på port 11434. På Railway: sæt OLLAMA_BASE_URL=http://<DENNE-VPS-IP>:11434"
