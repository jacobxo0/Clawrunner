# Cloud deployment runbook — sæt OpenClaw op til cloud-kørsel

Trin-for-trin så gateway, Telegram og cron kører på en VPS. Udfør i rækkefølge.

---

## Forudsætninger

- Du har en VPS med Ubuntu 22.04 (fx Hetzner CX) og SSH-adgang (bruger fx `ubuntu`).
- Fra din Windows-PC kan du køre `ssh ubuntu@DIN_VPS_IP` og evt. `scp`/`rsync` (eller WSL med rsync).

**Pre-flight tjekliste:** [notes/cloud-preflight.md](c:\Users\Jnkri\.openclaw\notes\cloud-preflight.md) — tjek at du har VPS-IP, SSH-adgang, og har noteret gateway token + Brave key før du starter.

---

## Del A: På VPS — basis og OpenClaw

**1. Log ind på VPS og opdater systemet**

```bash
ssh ubuntu@DIN_VPS_IP
sudo apt update && sudo apt upgrade -y
```

**2. Installér Node.js 22 og npm**

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v   # skal vise v22.x
```

**3. Installér OpenClaw globalt**

```bash
sudo npm install -g openclaw
openclaw --version
```

**4. Opret mappestruktur**

```bash
mkdir -p ~/openclaw/workspace ~/openclaw/cron ~/openclaw/scripts
```

---

## Del B: Fra Windows — kopiér config og workspace til VPS

**5. Rediger openclaw.json til cloud (workspace-sti)**

På din PC: lav en kopi til cloud med Linux-workspace-sti (eller rediger efter upload). I `openclaw.json` skal `agents.defaults.workspace` være den sti der gælder på VPS, fx:

```json
"workspace": "/home/ubuntu/openclaw/workspace"
```

Gem som fx `openclaw.cloud.json` eller rediger efter scp.

**6. Upload openclaw.json, cron, scripts og workspace**

**Nem løsning (PowerShell, én kommando):** Fra OpenClaw-roden (`C:\Users\Jnkri\.openclaw`):

```powershell
.\scripts\upload-to-vps.ps1 -VpsIp "DIN_VPS_IP" -VpsUser "ubuntu"
```

Scriptet laver automatisk en openclaw.json med Linux workspace-sti og uploader config, cron, scripts og hele workspace.

**Manuel upload** (hvis du foretrækker det):

```powershell
# Erstatt DIN_VPS_IP og evt. ubuntu med din bruger
scp openclaw.json ubuntu@DIN_VPS_IP:~/openclaw/openclaw.json
scp cron/jobs.json ubuntu@DIN_VPS_IP:~/openclaw/cron/
scp scripts/start-gateway.sh scripts/.env.cloud.example ubuntu@DIN_VPS_IP:~/openclaw/scripts/
scp -r workspace/* ubuntu@DIN_VPS_IP:~/openclaw/workspace/
```

Alternativ med rsync (fra WSL eller Git Bash med rsync):

```bash
rsync -avz --exclude '.venv' --exclude 'node_modules' /mnt/c/Users/Jnkri/.openclaw/workspace/ ubuntu@DIN_VPS_IP:~/openclaw/workspace/
```

**7. På VPS: ret workspace-sti i openclaw.json**

SSH ind på VPS og tjek at `~/openclaw/openclaw.json` har:

```json
"agents": {
  "defaults": {
    "workspace": "/home/ubuntu/openclaw/workspace",
    ...
  }
}
```

(Erstatt `/home/ubuntu` med din bruger hvis anderledes.)

**8. Opret .env på VPS**

På VPS:

```bash
cd ~/openclaw
cp scripts/.env.cloud.example .env
nano .env   # eller vi
```

Sæt mindst:

- `OPENCLAW_GATEWAY_TOKEN=` samme værdi som i din nuværende openclaw.json under `gateway.auth.token`
- `BRAVE_API_KEY=` din Brave API-nøgle (samme som i openclaw.json under tools.web.search.apiKey)

Gem og luk. Beskyt: `chmod 600 .env`.

**9. Sæt OpenClaw til at læse config fra ~/openclaw**

OpenClaw læser typisk `~/.openclaw/openclaw.json`. For at bruge `~/openclaw` som rod:

- Enten: opret symlink: `ln -s ~/openclaw/openclaw.json ~/.openclaw/openclaw.json` (og opret `~/.openclaw` hvis nødvendigt), og sørg for at workspace-stien i json er absolut (fx `/home/ubuntu/openclaw/workspace`).
- Eller: kør altid fra `~/openclaw` med miljøvariabel. På Linux kan OpenClaw bruge `OPENCLAW_CONFIG_DIR` eller tjekke current working directory. Dokumentation: prøv `export OPENCLAW_CONFIG_DIR=$HOME/openclaw` før `openclaw gateway`.

Hvis OpenClaw kun læser fra `~/.openclaw`, så kopiér config og opret workspace-symlink:

```bash
mkdir -p ~/.openclaw
cp ~/openclaw/openclaw.json ~/.openclaw/
# I ~/.openclaw/openclaw.json skal workspace pege på /home/ubuntu/openclaw/workspace
```

---

## Del C: Start gateway på VPS

**10. Test-kør gateway manuelt**

```bash
cd ~/openclaw
source .env
export OPENCLAW_GATEWAY_PORT=18789
openclaw gateway --port 18789
```

Hold terminalen åben; tjek at der ikke kommer fejl. Tryk Ctrl+C når du har bekræftet at den starter. Telegram modtager kun beskeder når gatewayen kører; nu tester vi først at den starter.

**11. Kør gateway som systemd-service (så den kører efter reboot)**

På VPS:

```bash
# Find openclaw-binary (ofte /usr/local/bin/openclaw)
which openclaw
# Hvis det er andet end /usr/local/bin/openclaw, rediger service-filen: ExecStart=DEN_FULDE_STI gateway --port 18789

# Tilpas User= og paths hvis du ikke bruger bruger 'ubuntu'
sudo cp ~/openclaw/scripts/openclaw-gateway.service /etc/systemd/system/
sudo sed -i 's/ubuntu/DIT_BRUGERNAVN/g' /etc/systemd/system/openclaw-gateway.service   # hvis nødvendigt
sudo systemctl daemon-reload
sudo systemctl enable openclaw-gateway
sudo systemctl start openclaw-gateway
sudo systemctl status openclaw-gateway
```

Tjek at port 18789 lytter: `ss -tlnp | grep 18789`. Eller kør: `chmod +x ~/openclaw/scripts/verify-gateway-vps.sh && ~/openclaw/scripts/verify-gateway-vps.sh`.

**12. Åbn firewall for SSH (port 22) — behold 18789 lukket udadtil**

Hvis du kun forbinder via SSH-tunnel fra PC, behøver du ikke åbne 18789 på firewall. Ellers (fx Tailscale): åbn kun for din tailnet eller brug Tailscale Serve.

```bash
sudo ufw allow 22
sudo ufw enable
```

---

## Del D: Fra din PC — forbind til cloud-gateway

**13. SSH-tunnel fra Windows**

Fra en **ny** PowerShell/terminal på din PC (lad den køre):

```powershell
ssh -N -L 18789:127.0.0.1:18789 ubuntu@DIN_VPS_IP
```

Så peger localhost:18789 på din PC mod gatewayen på VPS.

**14. Test at gatewayen svarer**

I **anden** terminal på din PC (mens tunnellen kører):

```powershell
$env:OPENCLAW_GATEWAY_TOKEN = "DIN_GATEWAY_TOKEN"
openclaw cron list
```

Du bør se de 3 jobs (instant-mesh-build, instant-mesh-investor, instant-mesh-status).

**15. Telegram**

Samme Telegram-bot og token bruges på VPS. Så snart gatewayen kører på VPS, modtager og svarer botten som før. Test ved at sende en besked til botten i Telegram.

---

## Del E: Valgfrit — Tailscale på VPS

For at forbinde uden at holde SSH-tunnel åben: installér Tailscale på VPS, log ind på samme tailnet som din PC. Find VPS' Tailnet-IP (`tailscale ip -4`). På din PC kan du så sætte i openclaw.json (til remote mode):

```json
"gateway": {
  "mode": "remote",
  "remote": {
    "url": "ws://100.x.x.x:18789",
    "token": "DIN_GATEWAY_TOKEN"
  }
}
```

(Erstatt 100.x.x.x med VPS' Tailnet-IP.) Så behøver du ikke SSH-tunnel for at køre `openclaw cron list` osv.

---

## Fejlsøgning

- **Gateway starter ikke:** Tjek `.env` (OPENCLAW_GATEWAY_TOKEN sat?), `openclaw.json` i det rigtige sted, workspace-sti korrekt og mappe findes.
- **systemd: ExecStart fejler:** Kør `which openclaw` på VPS og brug den fulde sti i service-filen (ExecStart=...). Typisk `/usr/local/bin/openclaw`.
- **Telegram svarer ikke:** Gateway skal køre; tjek `systemctl status openclaw-gateway` og at port 18789 lytter. Samme botToken som lokalt.
- **Cron list virker ikke fra PC:** SSH-tunnel skal køre (Del D, trin 13), og OPENCLAW_GATEWAY_TOKEN skal være sat til samme som på VPS.

---

*Runbook oprettet 2026-03-06. Tilpas bruger-navn og VPS-IP til dit setup.*
