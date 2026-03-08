# OpenClaw kørende på cloud

Så gateway, Telegram og cron kan køre i skyen (VPS); lokale PC'er bruges som kontrol eller thin clients. Baseret på memory (cloud-only mål, ingen hardwarekøb, pay-as-you-go) og [workspace/notes/cloud-migration-plan.md](c:\Users\Jnkri\.openclaw\workspace\notes\cloud-migration-plan.md).

---

## Mål

- **Gateway + Telegram + cron** kører på en cloud-server (VPS), så Telegram svarer og cron kører selv når PC'en er slukket.
- **Lokale PC'er** forbinder sig til gatewayen via Tailscale eller SSH-tunnel (remote mode).
- **Ollama** kan køre på samme VPS (CPU) eller separat GPU-instans; valgfrit.
- **Workspace** ligger på VPS'en (synk eller kopi fra nuværende maskine); backup til ekstern disk eller cloud storage.

---

## Oversigt: hvad kører hvor

| Komponent      | Lokal (nu)     | Cloud (mål)        |
|----------------|----------------|--------------------|
| Gateway        | Din PC, port 18789 | VPS, port 18789 (eller bag Tailscale/SSH) |
| Telegram-bot   | Samme bot-token; gateway modtager beskeder hvor den kører | Samme token; gateway på VPS = bot svarer fra skyen |
| Cron           | Kun når gateway kører på PC  | Kører når gateway kører på VPS (24/7 muligt) |
| Workspace      | `C:\Users\Jnkri\.openclaw\workspace` | Fx `/home/bruger/openclaw/workspace` på VPS |
| Ollama         | Valgfrit lokalt | Valgfrit på VPS (samme maskine som gateway eller separat) |

---

## Trin 1: Vælg og provisioner VPS

- **Anbefaling:** Hetzner CX (CPU), Ubuntu 22.04. Alternativ: anden VPS med Ubuntu (evt. RunPod/Lambda til GPU hvis Ollama med store modeller).
- Installér på serveren: Node.js (v22+), git, OpenClaw (npm install -g openclaw), evt. Tailscale.
- Hardening: firewall (kun nødvendige porte), SSH-nøgle, evt. guide du bruger (fx "Aaron guide" fra cloud-migration-plan).

---

## Trin 2: OpenClaw og workspace på VPS

- Opret mappe fx `~/openclaw` (eller `/opt/openclaw`). Kopiér eller synkroniser:
  - **openclaw.json** (samme Telegram botToken, gateway auth token; ændr kun `gateway.bind` hvis nødvendig, se nedenfor).
  - **workspace/** — hele workspace-mappen (evt. rsync fra Windows, eller git clone hvis I bruger et repo).
  - **cron/jobs.json** (eller lad gatewayen genoprette ved første kørsel; ellers kopiér nuværende jobs).
  - **scripts/** (fx start-gateway – tilpas til Linux: `#!/bin/bash`, export env vars, `openclaw gateway --port 18789`).
- Sæt env vars på VPS: `OPENCLAW_GATEWAY_TOKEN`, `OPENCLAW_GATEWAY_PORT`, evt. `OLLAMA_API_KEY`, `BRAVE_API_KEY`.

---

## Trin 3: Gateway bind på VPS

- **Kun du selv (SSH/tailnet):** Behold `gateway.bind: "loopback"`. Forbind fra PC med SSH-tunnel:  
  `ssh -N -L 18789:127.0.0.1:18789 bruger@VPS_IP`  
  Så bruger du `openclaw` lokalt mod `ws://127.0.0.1:18789`.
- **Tailscale på VPS:** Installér Tailscale på VPS, log ind samme tailnet. Så kan du enten:
  - Sætte `gateway.bind: "tailnet"` så gateway lytter på VPS' Tailnet-IP (fx 100.x.x.x:18789), eller
  - Beholde loopback og bruge `openclaw gateway --tailscale serve` så Control UI og WebSocket er tilgængelige via Tailscale Serve.
- **Offentlig adgang (kun hvis du vil):** OpenClaw understøtter `tailscale.mode: "funnel"` med password-auth; brug kun med stærk adgangskode og forståelse af sikkerhed.

Telegram virker uanset bind: botten kalder Telegram API; det er gatewayens placering (VPS) der afgør at den kører 24/7.

---

## Trin 4: Start gateway på VPS

- På VPS, i openclaw-mappen:  
  `export OPENCLAW_GATEWAY_TOKEN="..."; export OPENCLAW_GATEWAY_PORT=18789; openclaw gateway --port 18789`  
  (Evt. kør via systemd eller screen/tmux så den kører efter SSH lukkes.)
- Tjek at port 18789 lytter: `ss -tlnp | grep 18789` eller `netstat -tlnp | grep 18789`.
- Fra din PC (med SSH-tunnel eller Tailscale): `openclaw cron list` — du bør se de samme jobs.

---

## Trin 5: Lokale PC'er som kontrol

- På ny/gammel PC: sæt **remote mode** i openclaw.json (eller brug env) så CLI peger på cloud-gatewayen:
  - Via SSH-tunnel: URL er `ws://127.0.0.1:18789` (lokal tunnel videresender til VPS).
  - Via Tailscale: URL er `ws://100.x.x.x:18789` (VPS' Tailnet-IP) med samme token.
- Så kan du køre `openclaw cron list`, `openclaw cron run <uuid>`, health osv. fra PC mod gatewayen i skyen.

---

## Trin 6: Ollama på cloud (valgfrit)

- Installér Ollama på samme VPS (eller en anden maskine på samme tailnet). Start `ollama serve`; pull modeller.
- På VPS hvor gatewayen kører: sæt `OLLAMA_API_KEY=ollama-local` og evt. `baseUrl` til Ollama-host (fx `http://127.0.0.1:11434` hvis samme maskine).
- Genstart gateway; `openclaw models list` skal vise Ollama-modeller. Derefter kan du sætte primary/fallback i openclaw.json som i [notes/ollama-setup.md](c:\Users\Jnkri\.openclaw\notes\ollama-setup.md).

---

## Trin 7: Backup (workspace + evt. config)

- Ekstern HDD: cron/skript på VPS der rsync'er eller tarrer workspace (og evt. openclaw.json) til mountet disk.
- Alternativ: backup til S3, Backblaze B2, eller anden cloud storage. Cloud-migration-plan nævner "backup job to external HDD".

---

## Kort svar til brugeren (Telegram / chat)

Når nogen spørger "kan det køre på cloud" eller "hvordan kører vi OpenClaw i skyen":

- **Ja.** Gateway + Telegram + cron kan køre på en VPS; samme bot-token, samme cron-jobs. Lokale PC'er forbinder sig med remote mode (SSH-tunnel eller Tailscale).
- **Fuld guide:** Denne fil (`notes/setup-openclaw-paa-cloud.md`) og `workspace/notes/cloud-migration-plan.md`. Trin: VPS → installér OpenClaw + kopiér workspace/config → start gateway → brug PC som remote-klient.

---

---

## Railway som alternativ til VPS

Du kan deploye gatewayen på **Railway** i stedet for en klassisk VPS: forbind dit GitHub-repo til Railway, sæt miljøvariabler (gateway-token, Telegram bot-token, Brave API key m.fl.), og brug Custom Start Command `bash scripts/railway-start.sh`. Ved push til den valgte branch bygger og starter Railway appen. Workspace og cron er ephemeral medmindre du tilknytter et Railway Volume.

**Fuld guide:** [notes/railway-deploy.md](railway-deploy.md).

---

## Konkret deployment nu

**Fuld trin-for-trin runbook med kopier-paste kommandoer:** [notes/cloud-deployment-runbook.md](c:\Users\Jnkri\.openclaw\notes\cloud-deployment-runbook.md). Der står præcis hvad du kører på VPS (Node, OpenClaw, mapper), hvad du uploader fra Windows (openclaw.json, workspace, cron, scripts), .env-opsætning, systemd-service og SSH-tunnel fra PC.

**Filer til cloud:** `scripts/start-gateway.sh`, `scripts/openclaw-gateway.service`, `scripts/.env.cloud.example`, `notes/openclaw-cloud-workspace-path.md`. **Railway:** `package.json`, `openclaw.railway.example.json`, `scripts/railway-start.sh`, [notes/railway-deploy.md](railway-deploy.md).

*Oprettet 2026-03-06. Udbyg evt. med konkrete kommandoer for dit valgte VPS-provider.*
