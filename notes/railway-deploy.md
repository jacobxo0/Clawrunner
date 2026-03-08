# Deploy OpenClaw gateway på Railway

Så du kan pushe til GitHub og lade Railway bygge og køre gatewayen. Telegram og cron kører når appen kører; workspace og cron-data er ephemeral medmindre du tilknytter et Volume.

---

## Forudsætninger

- Et GitHub-repo med OpenClaw-koden (denne mappe); forbundet til Railway.
- Railway bruger Node 20+ (angivet i `package.json` under `engines.node`).
- Du har værdierne til gateway-token, Telegram bot-token og evt. Brave API key.

---

## Trin 1: Opret projekt på Railway

1. Gå til [railway.app](https://railway.app) og log ind.
2. **New Project** → **Deploy from GitHub repo**.
3. Vælg dit repo og (evt.) den branch der skal deployes (fx `main`).
4. Railway genkender `package.json` og kører `npm install` som build.

---

## Trin 2: Sæt miljøvariabler

I Railway: **Project** → dit service → **Variables**. Tilføj:

| Variabel | Påkrævet | Beskrivelse |
|----------|----------|-------------|
| `OPENCLAW_GATEWAY_TOKEN` | Ja | Gateway auth-token (samme som i din lokale `openclaw.json` under `gateway.auth.token`). |
| `TELEGRAM_BOT_TOKEN` | Ja (hvis Telegram) | Telegram bot-token fra BotFather. |
| `TELEGRAM_GROUP_ALLOW_FROM` | Anbefalet | JSON-array med tilladte Telegram user-id’er, fx `["8572521981"]`. |
| `BRAVE_API_KEY` | Anbefalet | API-nøgle til web search (Brave). |
| `GITHUB_TOKEN` | Valgfrit | Til GitHub-skill. |
| `GITHUB_USERNAME` | Valgfrit | Til GitHub-skill. |
| `OLLAMA_BASE_URL` | Valgfrit | Når Ollama kører på en VPS: `http://<VPS-IP>:11434`. Gatewayen bruger så VPS-Ollama. Lad stå tom hvis du ikke bruger Ollama. |
| `OLLAMA_API_KEY` | Valgfrit | Fx `ollama-vps` når du bruger OLLAMA_BASE_URL. |

**Bemærk:** `PORT` sættes automatisk af Railway – du skal ikke tilføje den selv.

### Checkliste: Hvor finder du værdierne?

Kopiér fra din lokale **`openclaw.json`** (samme mappe som denne note) ind i Railway Variables:

| Railway variable | I openclaw.json |
|------------------|------------------|
| `OPENCLAW_GATEWAY_TOKEN` | `gateway.auth.token` |
| `TELEGRAM_BOT_TOKEN` | `channels.telegram.botToken` |
| `TELEGRAM_GROUP_ALLOW_FROM` | `channels.telegram.allowFrom` – skal være JSON, fx `["8572521981"]` |
| `BRAVE_API_KEY` | `tools.web.search.apiKey` |
| `GITHUB_TOKEN` | `skills.entries.github.env.GITHUB_TOKEN` |
| `GITHUB_USERNAME` | `skills.entries.github.env.GITHUB_USERNAME` |

`OLLAMA_BASE_URL`: sæt kun hvis Ollama kører på en VPS – `http://<VPS-IP>:11434`. Se [notes/plan-ollama-paa-vps.md](plan-ollama-paa-vps.md). `OLLAMA_API_KEY`: fx `ollama-vps`.

---

## Trin 3: Start-kommando

Repo indeholder **railway.toml** med `startCommand = "bash scripts/railway-start.sh"`. Railway bruger den automatisk – du behøver ikke sætte Custom Start Command i dashboard.

Hvis du ikke bruger railway.toml: I Railway **Settings** → **Deploy** → **Custom Start Command** kan du sætte `bash scripts/railway-start.sh`. Uden det kører Railway `npm start`, som kun starter gatewayen uden at bygge `openclaw.json` fra template.

---

## Trin 4: Deploy

- **Push til den valgte branch** (fx `main`). Railway bygger og deployer automatisk.
- Tjek **Deployments** og **Logs** for at se at gatewayen starter uden fejl.

### Følge build-logs live (så agenten kan rette fejl)

1. **Railway CLI → fil i workspace**  
   Installér Railway CLI: `npm i -g @railway/cli`. Log ind og link til projektet (fx `railway link`). Kør derefter:
   ```powershell
   .\scripts\railway-logs-to-workspace.ps1
   ```
   Scriptet henter de seneste build- og deploy-logs til **`logs/railway-latest.txt`**. Agenten kan læse den fil og rette fejl (fx JSON parse, manglende env).

2. **Efter push: agenten kører log-script**  
   Når agenten selv deployer (commit + push), bør den herefter køre `railway-logs-to-workspace.ps1`, læse `logs/railway-latest.txt` og rette eventuelle fejl i samme ombæring.

3. **Manuelt: del log eller screenshot**  
   Hvis du ikke bruger CLI: Åbn Railway → Deployments → vælg seneste → **View Logs**. Ved fejl kan du paste log-udtog eller dele et screenshot her i chatten – så kan agenten fejlsøge og lave fix + nyt push.

---

## Når deploy er kørt (efter push eller Restart)

**A. Verificer at deploy lykkedes**

- Railway Dashboard → Deployments → seneste deployment skal være grøn.
- View Logs: tjek at der står "openclaw.json genereret fra template" og at gatewayen starter uden exit (ingen "OPENCLAW_GATEWAY_TOKEN ikke sat" eller crash).
- Lokalt (hvis Railway CLI er linket): kør `.\scripts\railway-logs-to-workspace.ps1` og læs `logs/railway-latest.txt`.

**B. Domæne og Telegram (første gang, eller ved nyt domæne)**

- Settings → Networking → **Generate Domain** (fx `xxx.up.railway.app`). Notér URL.
- Sæt Telegram webhook: `https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://<DIT_DOMÆNE>/telegram` (curl eller browser; token fra Railway Variables).

**C. Test fra PC**

- Samme token som `OPENCLAW_GATEWAY_TOKEN` i Railway.
- PowerShell: `$env:OPENCLAW_GATEWAY_TOKEN="<token>"; openclaw --gateway https://<DIT_DOMÆNE> cron list` — forventet: liste over jobs eller tom, ingen Unauthorized.
- Send besked til botten i Telegram og tjek at den svarer.

**D. Forventet i logs (ikke fejl)**

- "Eligible: 4", "Missing requirements: 47" — forventet; se Fejlsøgning nedenfor. Ingen handling.

---

## Trin 5: Domæne og adgang

- Under **Settings** → **Networking** kan du **Generate Domain**. Du får en URL (fx `xxx.up.railway.app`).
- Gatewayen eksponerer typisk WebSocket/API på den port Railway tildeler; Railway routerer trafik til din app – du bruger kun domænet uden port i URL.

For at bruge gatewayen fra din PC: brug den genererede URL som gateway-URL og samme `OPENCLAW_GATEWAY_TOKEN` som du sat i Railway.

### Live gateway (Clawrunner)

| | |
|--|--|
| **Public URL** | **https://clawrunner.railway.app** |
| **Port** | Railway injicerer PORT internt; du bruger kun domænet i URL. |

**Telegram webhook** — URL: `https://clawrunner.railway.app/telegram`

- **Option A (curl):** Erstatt `<TELEGRAM_BOT_TOKEN>` med værdien fra Railway Variables → TELEGRAM_BOT_TOKEN.
  ```bash
  curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
    -d "url=https://clawrunner.railway.app/telegram"
  ```
- **Option B (BotFather):** I Telegram: skriv til @BotFather → send `/setwebhook` → angiv URL: `https://clawrunner.railway.app/telegram`.

**OpenClaw CLI** — peg mod Railway-gatewayen fra din PC:

- Base URL: `https://clawrunner.railway.app`
- Token: samme værdi som `OPENCLAW_GATEWAY_TOKEN` i Railway Variables.
- Eksempel (erstat `<token>` og `<command>`):
  ```bash
  OPENCLAW_GATEWAY_TOKEN="<token>" openclaw --gateway https://clawrunner.railway.app <command>
  ```
  Fx: `OPENCLAW_GATEWAY_TOKEN="<token>" openclaw --gateway https://clawrunner.railway.app cron list`

---

## Workspace og cron (persistering)

- Railway’s filsystem er **ephemeral**: ved redeploy kan alt under app-mappen nulstilles.
- **Railway Volumes:** For at bevare workspace og evt. `cron` mellem deploys kan du tilknytte et Volume og montere det fx på `/app/workspace` (og evt. `/app/cron`). Opret Volume i Railway og sæt mount path til `/app/workspace` (så matcher det `agents.defaults.workspace` i template).
- Uden Volume: workspace og cron-jobs er midlertidige og kan forsvinde ved redeploy – brug det til test eller accepter at de ikke persisteres.

---

## Fejlsøgning

**Debug i Deploy Logs:** Start-scriptet skriver `[DEBUG]`-linjer så du kan se hvor langt det når. Rækkefølge: `ROOT/PWD` → `PORT` → token sat → openclaw.json genereret → workspace/cron OK → .openclaw OK → openclaw --version check → `Starting OpenClaw gateway on port X`. Stopper det før "Starting OpenClaw gateway", er fejlen i det trin der mangler. Når gatewayen starter men containeren crasher alligevel, viser scriptet nu **`[FATAL] Gateway exited with code N`** — exit-kode 1 = fejl, 137 = OOM kill, 139 = segfault. Tjek også for Node/JavaScript-stack traces lige før den linje.

- **"Build failed" / "Error creating build plan with Railpack":**
  - Repo har nu en **Dockerfile**. Railway vælger automatisk Docker-build når Dockerfile findes – det omgår Railpack. Commit Dockerfile og .dockerignore, push igen.
  - **Build-loggen:** Gå til Deployment → vælg den røde build → se **Build logs**. Fejler det under `npm install` (fx "404 Not Found" på openclaw), er pakkenavnet forkert. Fejler det under **Deploy** (efter build), er det start-scriptet eller env.
  - **CRLF:** Hvis loggen viser bash-fejl (fx `\r: command not found`), skal shell-scripts have LF. Brug `.gitattributes` med `*.sh text eol=lf` og evt. `git add --renormalize .`.
  - **Manglende env:** Hvis fejlen er "OPENCLAW_GATEWAY_TOKEN ikke sat", er det **Deploy**-fasen – sæt alle Variables (se Trin 2) før næste deploy.
- **Gateway starter ikke:** Tjek at `OPENCLAW_GATEWAY_TOKEN` og `TELEGRAM_BOT_TOKEN` er sat og at start-kommandoen er `bash scripts/railway-start.sh`.
- **Telegram svarer ikke:** Tjek at bot-token er korrekt og at `TELEGRAM_GROUP_ALLOW_FROM` er et gyldigt JSON-array (fx `["12345678"]`).
- **Port:** Du må ikke hardcode port; brug altid `$PORT` (scriptet gør det).
- **"JavaScript heap out of memory":** Start-scriptet sætter nu `NODE_OPTIONS=--max-old-space-size=1024` (1 GB). Hvis det stadig crasher: øg **Service memory** i Railway (Settings → Resources), eller sæt i Variables fx `NODE_OPTIONS=--max-old-space-size=1536`.
- **"Missing requirements: 47" / "Eligible: 4":** Normalt på Railway. OpenClaw kender mange skills; kun de 4 har opfyldte krav (env, tools) i containeren. Gatewayen kører fint med de eligible; resten bruges ikke.

---

## Filer i repo der bruges

- `Dockerfile` – Railway bygger med Docker (undgår Railpack-fejl); kører `scripts/railway-start.sh`.
- `.dockerignore` – udelukker node_modules, .git, openclaw.json så build er ren.
- `package.json` – dependency på `openclaw`, start-script.
- `openclaw.railway.example.json` – config-template med placeholders; bruges af `railway-start.sh`.
- `scripts/railway-start.sh` – bygger `openclaw.json` fra env, opretter `workspace`/`cron`, starter `openclaw gateway --port $PORT`.

**Script kørbart på Linux:** Hvis du cloner på Windows og Railway bygger derfra, skal scriptet være kørbart. Kør én gang lokalt (inden push): `git update-index --chmod=+x scripts/railway-start.sh` og commit – så er det executable i repo og på Railway.

VPS-alternativ (fuld kontrol, persisteret disk): [notes/cloud-deployment-runbook.md](cloud-deployment-runbook.md).
