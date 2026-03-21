# Start her: OpenClaw på cloud

Sæt det hele op til cloud-kørsel i én rækkefølge.

---

## 1. Du har brug for

- En VPS med Ubuntu 22.04 (fx Hetzner CX) og SSH-adgang.
- Din nuværende OpenClaw-mappe (openclaw.json, workspace, cron, scripts) på Windows.

---

## 2. Fuld runbook (alle kommandoer)

Åbn og følg **trin for trin**:

**[notes/cloud-deployment-runbook.md](c:\Users\Jnkri\.openclaw\notes\cloud-deployment-runbook.md)**

Der står:

- **Del A:** På VPS — installér Node 22, OpenClaw, opret mapper.
- **Del B:** Fra Windows — upload openclaw.json (med Linux workspace-sti), workspace, cron, scripts; opret .env på VPS.
- **Del C:** På VPS — start gateway (test, derefter systemd så den kører efter reboot).
- **Del D:** Fra PC — SSH-tunnel, test med `openclaw cron list`, tjek Telegram.
- **Del E:** Valgfrit — Tailscale så du ikke behøver holde tunnel åben.

---

## 3. Filer der er lavet til cloud

| Fil | Formål |
|-----|--------|
| `scripts/upload-to-vps.ps1` | **Fra Windows:** Upload alt til VPS (openclaw.json med Linux-sti, cron, scripts, workspace). Kør: `.\scripts\upload-to-vps.ps1 -VpsIp "IP" -VpsUser "ubuntu"` |
| `scripts/start-gateway.sh` | Start gateway på Linux (VPS); læser .env. |
| `scripts/openclaw-gateway.service` | Systemd-unit så gatewayen kører som tjeneste og genstarter ved fejl. |
| `scripts/.env.cloud.example` | Eksempel på .env; kopiér til VPS som .env og udfyld token + Brave key. |
| `scripts/verify-gateway-vps.sh` | Kør på VPS efter start: tjekker at port 18789 lytter og processen kører. |
| `notes/cloud-preflight.md` | Tjekliste før du starter (VPS-IP, SSH, token, Brave key). |
| `notes/openclaw-cloud-workspace-path.md` | Hvordan workspace-stien sættes i openclaw.json på VPS. |

---

## 4. Kort flow

1. Provisioner VPS (Ubuntu 22.04).
2. Kør Del A på VPS (Node, OpenClaw, mapper).
3. Fra PC: upload config + workspace (Del B).
4. På VPS: .env, evt. ~/.openclaw så config læses, start gateway (Del C).
5. Fra PC: SSH-tunnel, test cron list og Telegram (Del D).

Når det er gjort, kører gateway og Telegram fra skyen; cron kører på plan; du styrer fra PC via tunnel eller Tailscale.
