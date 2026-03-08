# Setup: ny + gammel computer koblet til samme system

Baseret på det I har talt om i Telegram og memory (Ops Control UI, gammel PC, ny PC, cloud, ekstern disk). Én OpenClaw-instans, flere maskiner.

---

## Mål (fra Telegram / memory)

- **Central UI** (backend + web) til at styre alle programmeringsopgaver på tværs af:
  - gammel PC  
  - ny PC  
  - cloud  
  - ekstern disk / backups  
- Begge computere skal kunne bruge **samme** OpenClaw (samme Telegram, samme cron, samme workspace-logik).

---

## To veje til “samme system”

### Vej A: Én gateway, andre maskiner forbundet (anbefalet til “altid samme agent”)

- **Én maskine kører gatewayen** (fx ny PC eller en “altid-tændt” server).
- **Den anden maskine** (gammel PC) forbinder sig til gatewayen via:
  - **Tailscale** (begge på samme tailnet, gateway lytter på tailnet eller via Tailscale Serve), eller  
  - **SSH-tunnel** fra gammel PC til ny PC: `ssh -N -L 18789:127.0.0.1:18789 bruger@ny-pc`.
- **Workspace** kan ligge på den maskine hvor gatewayen kører; gammel PC bruger så kun CLI/WebChat mod gateway (ingen lokal workspace nødvendig), eller I synkroniserer workspace (cloud/disk) og kun gateway-host bruger den aktive mappe.

**Fordele:** Én Telegram-bot, én cron, én session. Du kan skrive fra Telegram uanset hvilken PC du sidder ved.

---

### Vej B: Samme workspace på begge, én gateway ad gangen

- **Workspace synkroniseres** mellem ny PC, gammel PC og evt. cloud/ekstern disk (OneDrive, Dropbox, rsync, eller fælles netværksdisk).
- **Kun én maskine kører gatewayen** ad gangen (fx den du arbejder på). Når du skifter PC, stopper du gateway på den ene og starter på den anden.
- **Samme `openclaw.json`** (eller næsten samme) på begge – fx gemt i den synkroniserede mappe, så begge bruger samme token, cron, Telegram-bot.

**Fordele:** Simpelt, ingen Tailscale/SSH nødvendig. Ulempe: Telegram/cron virker kun mens den PC kører hvor gatewayen er startet.

---

## Konkret: Vej A med Tailscale (ny + gammel på samme netværk)

1. **Installér Tailscale** på både ny PC og gammel PC. Log ind på samme Tailnet.
2. **Beslut hvor gatewayen skal køre** (fx ny PC). På den maskine:
   - Enten **bind til Tailnet-IP** så gammel PC kan nå den direkte:
     - I `openclaw.json` under `gateway`: sæt `"bind": "tailnet"` (og behold `auth.token`). Find Tailnet-IP med `tailscale ip -4`.
     - Start gateway som nu; den lytter på Tailnet-IP:18789.
   - Eller **behold loopback og brug Tailscale Serve** (gateway forbliver kun på 127.0.0.1, Tailscale giver HTTPS + routing):
     - I `openclaw.json`: `gateway.tailscale.mode`: `"serve"` (og `bind`: `"loopback"`).
     - Start med: `openclaw gateway --tailscale serve` (eller tilsvarende så Serve er aktiveret).
3. **På gammel PC:**  
   - Sæt `openclaw.json` til **remote**: `gateway.mode`: `"remote"`, `gateway.remote.url`: `ws://<Tailnet-IP-af-ny-PC>:18789` (eller HTTPS-URL fra Serve), `gateway.remote.token`: samme token som på ny PC.  
   - Brug herefter `openclaw`-kommandoer mod den fjerne gateway; WebChat/Telegram bruger stadig gatewayen på ny PC.
4. **Workspace:** Enten kun på gateway-host, eller synkroniseret mellem begge (så agenten altid arbejder mod samme filer, uanset hvilken PC du åbner fra).

---

## Ops Control UI (central styring)

Fra memory: *“Skal bygge et central UI (backend + web) til at styre alle programmeringsopgaver på tværs af gammel PC, ny PC, cloud og ekstern disk backups.”*

- Det kan bygges som **udvidelse af det nuværende dashboard** (`dashboard/index.html` / den planlagte Vite+Tailwind-app) med:
  - Oversigt over hvilken maskine der kører gateway (evt. node-status).
  - Links/triggers til opgaver på tværs af projekter (Instant Mesh, NFT-arbitrage, reklame-generator).
  - Evt. visning af backup/disk-status (ekstern disk, cloud sync).
- **Backend:** Kan kalde OpenClaw gateway API (fx health, cron list, evt. spawn) så UI’et styrer den samme gateway som Telegram/cron.

Dette står som næste skridt i CHECKLIST (Dashboard / Control Center). Når ny+gammel-computer-setup kører, kan Ops Control UI bygges oven på samme gateway.

---

## Kort reference: openclaw.json (Tailscale / remote)

**På maskinen der kører gateway (fx ny PC), hvis du vil bruge Tailscale Serve:**

```json
"gateway": {
  "port": 18789,
  "mode": "local",
  "bind": "loopback",
  "auth": { "mode": "token", "token": "..." },
  "tailscale": {
    "mode": "serve",
    "resetOnExit": false
  }
}
```

Start: `openclaw gateway --tailscale serve` (Tailscale CLI skal være installeret og logget ind).

**På gammel PC (kun klient mod ny PC):**

```json
"gateway": {
  "mode": "remote",
  "remote": {
    "url": "https://<din-serve-hostname>/",
    "token": "samme-token-som-ny-PC"
  }
}
```

(Erstatt URL med den Tailscale Serve-URL du får, eller med `ws://<tailnet-ip>:18789` hvis du bruger `bind: "tailnet"`.)

---

## Næste skridt

1. **Vælg vej:** A (én gateway, Tailscale/SSH) eller B (synkroniseret workspace, én gateway ad gangen).
2. **Hvis A:** Installér Tailscale på begge PC’er; sæt gateway til `bind: "tailnet"` eller `tailscale.mode: "serve"` på den maskine der hoster; sæt remote på den anden.
3. **Ops Control UI:** Prioriter i dashboard/CHECKLIST så det central UI kommer til at styre opgaver på tværs af maskiner og backups.

Sidst opdateret: 2026-03-06. Baseret på memory (Ops Control UI, multi-PC) og OpenClaw docs (Tailscale, remote).
