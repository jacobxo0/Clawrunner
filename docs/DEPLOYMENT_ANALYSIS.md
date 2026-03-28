# DEPLOYMENT_ANALYSIS.md
# OpenClaw Gateway — Deployment på Railway + Hetzner: Teknisk Analyse

> **Udarbejdet:** 2026-03-28
> **Stack:** OpenClaw `2026.3.22` · Railway Hobby · Hetzner `ubuntu-8gb-nbg1-1` · Groq llama-3.3-70b · Ollama llama3.2
> **Formål:** Post-mortem analyse af produktionsfejl + fremadrettet stabilitetsvejledning

---

## Indholdsfortegnelse

1. [Overblik & Vurdering](#1-overblik--vurdering)
2. [Fejlanalyse — hvad gik galt og hvorfor](#2-fejlanalyse--hvad-gik-galt-og-hvorfor)
3. [Platform-sammenligning: Railway vs alternativer](#3-platform-sammenligning-railway-vs-alternativer)
4. [Telegram: Polling vs Webhook](#4-telegram-polling-vs-webhook)
5. [LLM-model valg](#5-llm-model-valg)
6. [Hetzner server-vurdering](#6-hetzner-server-vurdering)
7. [Stabilitetstjekliste](#7-stabilitetstjekliste-)
8. [Anbefalet målarkitektur](#8-anbefalet-målarkitektur)
9. [Hurtige wins (kan gøres i dag)](#9-hurtige-wins-kan-gøres-i-dag)

---

## 1. Overblik & Vurdering

### Samlet vurdering

Det aktuelle setup er funktionelt, men bærer præg af at være en iterativ bootstrap-løsning frem for en gennemtænkt produktionsarkitektur. De syv fejl der er opstået er næsten alle **forudsigelige og forebyggelige** — de fleste skyldes en manglende match mellem platform-antagelser (Railway) og software-antagelser (OpenClaw + Telegram long-polling).

**Positivt:**
- OpenClaw gateway med Groq som primær LLM er et kosteffektivt og hurtigt setup
- Hetzner-instansen er solidt funderet til Ollama-workloads
- Watchdog-loop og Telegram-notifikationer er implementeret — det er proaktiv selvovervågning
- `restartPolicyType = ON_FAILURE` er på plads

**Problematisk:**
- Telegram long-polling er fundamentalt inkompatibelt med containeriserede rolling deploys
- Groq llama-3.3-70b-versatile er upålidelig til structured function calling — dette er et kritisk svaghedspunkt for en AI agent
- Der er ingen ekstern monitoring — botfejl opdages først når brugeren selv melder det (eller via Telegram)
- Den "stille polling-drop" (Fejl 6) er udiagnosticeret og kan gentage sig uden varsel

### Er Railway det rigtige valg?

**Kortsvaret: Ja, men med forbehold.**

Railway Hobby-planen ($5 kredit/måned) er tilstrækkelig til en low-traffic Telegram bot. Problemet er ikke Railway som platform — problemet er at **long-polling Telegram bots er dårligt egnet til enhver container-platform med rolling deploys**, uanset om det er Railway, Render, Fly.io eller andet.

Railway har følgende relevante begrænsninger for dette use case:
- Rolling deploys = overlap-vindue = Telegram 409 Conflict (se Fejl 3)
- Ingen native support for "drain old instance before starting new" i Hobby-planen
- Healthcheck-konfiguration kræver kendskab til hvad gateway'en faktisk eksponerer

Hvis botten forbliver på Railway, **er webhook den eneste holdbare løsning** til at eliminere 409-problemet.

### Er Hetzner stor nok?

**Kortsvaret: Ja, til nuværende workload. Men det er snævert.**

`ubuntu-8gb-nbg1-1` (8GB RAM, 4 vCPU shared) er tilstrækkelig til Ollama + llama3.2:latest som backup, men der er ikke meget headroom. Se [sektion 6](#6-hetzner-server-vurdering) for detaljeret analyse.

---

## 2. Fejlanalyse — hvad gik galt og hvorfor

### Kronologisk fejloverblik

| # | Fejl | Årsag | Symptom | Fix | Forebyggelse |
|---|------|--------|---------|-----|--------------|
| 1 | `gateway.bind="loopback"` | OpenClaw default-config binder til 127.0.0.1 | Railway healthcheck/routing når ikke gateway | Sæt `gateway.bind = "all"` i openclaw.json | Altid eksplicit konfigurere bind-adresse i container-deployments. Default loopback er korrekt lokalt, forkert i container |
| 2 | `railway.toml` startCommand forkert | CMD i Dockerfile og `startCommand` i railway.toml konflikter; forkert subcommand (`openclaw gateway` i stedet for `openclaw gateway run`) | Gateway starter ikke | `startCommand = "bash scripts/railway-start.sh"` med korrekt subcommand | Dokumenter at Railway `startCommand` **overrider** Dockerfile CMD. Test startcommand lokalt med `docker run` |
| 3 | Telegram 409 Conflict | To bot-instanser poller simultant under Railway rolling deploy overlap + fejlet deploy holdt gammel instans i live | `getUpdates conflict: 409` — eksponentiel backoff loop, stuck 30s for evigt. ~3 dage nedetid | `deleteWebhook` API-kald for at rydde Telegram state, derefter force redeploy | **Skift til webhook** (eliminerer problemet fuldstændigt). Alternativt: `deleteWebhook` + force restart som del af deploy-script |
| 4 | Healthcheck blokerer deployment | `healthcheckPath = "/"` tilføjet i railway.toml — OpenClaw gateway eksponerer IKKE HTTP GET `/` | "1/1 replicas never became healthy! Healthcheck failed!" | Fjern `healthcheckPath` fra railway.toml | Verificer altid hvilke HTTP-endpoints en service faktisk eksponerer inden healthcheck konfigureres. Brug `curl` lokalt mod kørende container |
| 5 | Groq "Failed to call a function" | llama-3.3-70b-versatile på Groq genererer ikke valid JSON til function/tool calling | `error=Failed to call a function. Please adjust your prompt. See 'failed_generation'` | — (ingen permanent fix endnu) | Skift til `llama-3.1-8b-instant` eller `mixtral-8x7b` til tool-use, eller brug Anthropic claude-haiku som fallback model for structured calls |
| 6 | Silent polling drop | Ukendt — sandsynligvis TCP keepalive timeout på Telegram long-poll forbindelse | Bot deployet OK, ingen crash-logs, men stopper med at svare. ~1 time udetektet nedetid | Force redeploy | Ekstern monitoring: cron-job der sender `/ping` til bot hvert 10. minut og alarmerer ved manglende svar |
| 7 | OpenClaw respawn crash (dev) | `openclaw gateway run` exits code 1 med respawn failure ved entry.js:372 i no-TTY container-miljø | Process dør ved opstart i Railway container | Opdater til version ≥ 2026.3.22 (fixet) | Hold openclaw opdateret. Pin version eksplicit i package.json og test efter opdatering |

### Dybdegående analyse: Fejl 3 (Telegram 409) — den kritiske fejl

Denne fejl fortjener særlig opmærksomhed fordi den forårsagede ~3 dages nedetid og er **strukturelt betinget** — den vil gentage sig ved enhver redeploy så længe long-polling bruges.

**Hvad sker der præcist:**

```
T+0s:   Railway starter ny instans (v2)
T+1s:   v2 begynder getUpdates polling
T+1s:   v1 (gammel instans) poller stadig
T+2s:   Telegram returnerer 409 til begge
T+2s:   OpenClaw v1 starter exponential backoff: 2s
T+4s:   Railway sender SIGTERM til v1
T+4s:   v1 ignorerer/fejler SIGTERM (node process cleanup)
T+6s:   Railway sender SIGKILL
T+6s:   v1 dræbt. v2 har nu eksklusiv polling
--- Men hvis deploy fejler ---
T+0s:   Railway starter ny instans (v2) — fejler ved startup
T+1s:   v2 crasher
T+1s:   v1 er allerede i backoff-loop (2s → 4s → 8s → 30s)
T+∞:    v1 kører men poller aldrig igen (fast i 30s-loop)
```

Det eksponentielle backoff-mønster i OpenClaw stopper IKKE selv — det plateauer ved 30 sekunder og fortsætter for evigt. Den eneste recovery er:
1. `deleteWebhook` API-kald (rydder Telegram's server-side state)
2. Genstart af OpenClaw-processen

**Forebyggelse på deploy-niveau:**

```bash
# scripts/railway-start.sh — tilføj dette FØR gateway start
echo "Clearing Telegram webhook/polling state..."
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" | jq .

echo "Starting OpenClaw gateway..."
exec openclaw gateway run
```

---

## 3. Platform-sammenligning: Railway vs alternativer

### Evalueringskriterier for Telegram polling bots

En Telegram bot med long-polling har specifikke krav der adskiller sig fra standard web-services:

- **Always-on**: Ingen acceptable cold starts — polling stopper ved sleep
- **Single instance**: Telegram tillader kun én polling-forbindelse ad gangen
- **Hurtig genstart**: Ved crash skal bot genstartes inden brugeren bemærker det (< 30s)
- **Persistent TCP**: Long-poll kræver stabil langvarig TCP-forbindelse
- **Lav latens**: Svar til brugere bør komme inden for 1-3 sekunder

### Platformsammenligning

| Platform | Pris/md | Cold start | Always-on | Single instance garanti | Egnet til Telegram polling | Bemærkning |
|----------|---------|-----------|-----------|------------------------|--------------------------|------------|
| **Railway Hobby** | $5 kredit | Nej (deployed = always on) | Ja (inden for kredit) | Nej — rolling deploys giver overlap | ⚠️ Muligt med workarounds | Bruges nu. 409-risiko ved deploy |
| **Railway Pro** | $20+ | Nej | Ja | Nej — stadig rolling | ⚠️ Bedre SLA, samme strukturelle problem | Ikke nødvendigt for denne use case |
| **Hetzner CX22** | ~€4.5 | N/A (VPS) | Ja | Ja — du kontrollerer deploy | ✅ Optimal | Systemd service, ingen overlap |
| **Hetzner CX32** | ~€9 | N/A (VPS) | Ja | Ja | ✅ Optimal | Mere RAM til Ollama co-location |
| **Fly.io** | ~$1.94 (256MB) | Ja (kan konfigureres) | Nej per default | Nej — rolling deploys | ⚠️ Requires `min_machines_running = 1` | Webhook anbefales stærkt |
| **Render.com Free** | $0 | Ja (15 min sleep) | Nej | N/A | ❌ Uegnet | Sover = polling stopper |
| **Render.com Starter** | $7 | Nej | Ja | Nej — zero-downtime deploy | ⚠️ Muligt | Lignende Railway-problematik |
| **DigitalOcean Droplet** | ~$6 (1GB) | N/A (VPS) | Ja | Ja | ✅ God | Simpel, forudsigelig |
| **DigitalOcean App Platform** | $5+ | Nej | Ja | Nej — rolling deploys | ⚠️ Muligt | Samme 409-risiko |

### Railway Hobby — detaljeret fordele/ulemper

**Fordele:**
- Hurtig deployment fra Git-push (< 2 minutter typisk)
- Ingen server-administration
- Gratis inbound SSL/TLS (nødvendigt for webhook)
- Automatisk environment variables-håndtering
- God logging UI

**Ulemper for always-on bots:**
- Rolling deploys = guaranteed 409-vindue ved long-polling
- $5 kredit er ~500 compute-timer på en 512MB instans — nok, men pas på memory-spike
- Ingen cron-job på Hobby (skal håndteres eksternt)
- Ingen SSH-adgang til debugging

**Konklusion Railway:** Acceptabelt til webhook-baseret bot. Problematisk til polling-bot.

### Anbefalingen: Flyt til Hetzner eller brug webhook på Railway

**Scenarie A (mindst ændring):** Bliv på Railway, skift til webhook. Eliminerer 409-problemet.

**Scenarie B (maksimal kontrol):** Flyt OpenClaw til Hetzner-serveren. Ollama + OpenClaw på samme maskine. Ingen rolling deploy overlap. Direkte systemd-kontrol. Kræver nginx reverse proxy til webhook.

---

## 4. Telegram: Polling vs Webhook

### Hvad er forskellen?

**Long-polling:**
```
Bot → Telegram: "Giv mig opdateringer, vent i op til 30s"
Telegram → Bot: [array af updates efter 0-30s]
Bot → Telegram: "Giv mig opdateringer, vent i op til 30s"
... (uendeligt)
```

**Webhook:**
```
Telegram → Bot (HTTP POST): {"update_id": 123, "message": {...}}
Bot → Telegram: HTTP 200 OK
```

### Sammenligning

| Egenskab | Long-polling | Webhook |
|---------|--------------|---------|
| Infrastruktur | Kun udgående internet | Kræver HTTPS URL med valid cert |
| Single instance | Telegram håndhæver det IKKE — giver 409 | Telegram sender POST til én URL — ingen konflikt |
| Rolling deploys | ❌ Kritisk risiko for 409 | ✅ Ingen konflikt — ny instans overtager URL |
| Latens | ~50-200ms (polling interval) | ~50-100ms (direkte push) |
| Reconnect ved netværksfejl | Manuel backoff nødvendig | Telegram prøver automatisk igen |
| Debugging | Nemt (bare kig på logs) | Kræver HTTPS endpoint lokalt (ngrok/localtunnel) |
| Egnet til containers | ❌ Problematisk | ✅ Ideel |
| Egnet til serverless | ❌ Umuligt (ingen persistent connection) | ✅ Ideel |

### Hvorfor polling er problematisk i containeriserede miljøer

Containerplatforme som Railway, Fly.io og Render bruger alle **rolling deploys**: ny container starter, sundhedstjek godkendes, gammel container stoppes. Dette overlap-vindue er typisk 5-30 sekunder.

I den periode er der **to instanser der kører simultant**. For web-servere er dette uproblematisk — hver request håndteres af én instans. For Telegram long-polling er det katastrofalt:

1. Telegram tillader kun én `getUpdates`-session per bot-token
2. Begge instanser kalder `getUpdates` med samme token
3. Telegram returnerer 409 til begge
4. OpenClaw starter exponential backoff
5. Gammel instans slukkes af Railway — men er nu fast i backoff-loop
6. Ny instans er også i backoff-loop fra 409
7. Bot er effektivt død

Problemet er ikke kun ved deploy — det opstår også ved:
- Container-crash og auto-restart (Railway gennemtvinger restart)
- Manuelle force-deploys
- Railway platform-maintenance

### Konkret guide: Skift til webhook

#### Trin 1: Forbered Railway URL

Din Railway-service har automatisk en public URL. Find den:

```bash
# I Railway dashboard: Settings → Domains
# Format: https://<service-name>.railway.app
# Eksempel: https://clawrunner-production.railway.app
```

#### Trin 2: Sæt webhook via Telegram API

```bash
# Sæt webhook
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=https://clawrunner-production.railway.app/telegram/webhook" \
  -d "drop_pending_updates=true" \
  -d "max_connections=1" | jq .

# Verificer
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | jq .
```

#### Trin 3: Konfigurer OpenClaw til webhook

Ret `openclaw.json` (eller Railway env var):

```json
{
  "telegram": {
    "mode": "webhook",
    "webhookPath": "/telegram/webhook",
    "webhookSecret": "${TELEGRAM_WEBHOOK_SECRET}"
  },
  "gateway": {
    "bind": "all",
    "port": "${PORT}"
  }
}
```

#### Trin 4: Slet polling-state (kritisk!)

```bash
# Kør INDEN skift til webhook — rydder Telegram's polling-state
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
```

#### Trin 5: Opdater railway-start.sh

```bash
#!/bin/bash
set -e

# IKKE deleteWebhook her — vi bruger webhook nu
echo "Verifying webhook config..."
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('Webhook URL:', d['result'].get('url','NOT SET'))"

exec openclaw gateway run
```

#### Hvad sker der ved redeploy med webhook?

```
T+0s:   Railway starter ny instans (v2)
T+1s:   v2 starter — lytter på ${PORT}
T+5s:   Railway healthcheck godkendes (hvis konfigureret korrekt)
T+5s:   Railway retter traffic til v2
T+5s:   Telegram sender nu POST til v2
T+6s:   Railway sender SIGTERM til v1
T+7s:   v1 stopper rent
```

Ingen konflikt. Ingen 409. Ingen backoff-loop.

---

## 5. LLM-model valg

### Groq llama-3.3-70b-versatile

**Styrker:**
- Ekstremt hurtig inference (typisk < 500ms first token)
- Generøs gratis tier (op til 14.400 requests/dag, 131.072 tokens/minut)
- God reasoning-kapacitet generelt

**Svagheder (kritiske for dette use case):**

| Problem | Detalje | Impact |
|---------|---------|--------|
| Ustabil function calling | Genererer ikke konsistent valid JSON til tool-use | ❌ Kritisk — AI agent kan ikke kalde tools |
| Temperatur-sensitivitet | Lav temperatur hjælper men eliminerer ikke problemet | Workaround, ikke fix |
| Rate limits på 70B | 6.000 requests/dag på det store model | Kan nås ved aktiv brug |
| Kontekstvindue | 128k tokens — godt, men chunking nødvendig for lange sessioner | Lavt impact |

**Groq function calling: hvad sker der præcist?**

Groq's llama-3.3-70b eksponerer et OpenAI-kompatibelt function calling API. Men Llama-modellen er ikke trænet specifikt på Groq's tool-use format, og output er ikke deterministisk valideret. Fejlmeddelelsen `"Failed to call a function. Please adjust your prompt."` indikerer at modellen har genereret JSON der ikke matcher det forventede tool-schema.

**Mulige fixes (i prioriteret rækkefølge):**

1. **Skift til `llama-3.1-8b-instant` for tool-use** — paradoksalt nok er den mindre model mere stabil til structured output
2. **Brug `mixtral-8x7b-32768`** — generelt bedre function calling end Llama 3.3
3. **Brug Anthropic claude-haiku-3-5** som fallback ved function-call fejl
4. **Prompt engineering**: Tilføj eksplicit JSON-schema i system prompt

### Ollama på Hetzner 8GB: Modelvalg

**Hetzner CX32 memory budget:**

```
OS + systemd:          ~500 MB
Ollama daemon:         ~200 MB
OpenClaw (hvis flyt):  ~300 MB
Nginx (hvis webhook):  ~50 MB
Buffer:                ~950 MB
Tilgængelig til model: ~6.0 GB
```

**Modeloversigt for 8GB setup:**

| Model | Størrelse (Q4) | Passer? | Function calling | Kvalitet | Anbefaling |
|-------|---------------|---------|-----------------|---------|------------|
| llama3.2:1b | ~1 GB | ✅ Masser | Ringe | Lav | Kun til ultra-hurtig simple svar |
| llama3.2:3b | ~2 GB | ✅ OK | Acceptabel | Medium | God backup til simple opgaver |
| llama3.2:latest (8B) | ~5 GB | ✅ Snævert | God | Høj | **Anbefalet primary** |
| qwen2.5:7b | ~4.7 GB | ✅ OK | Meget god | Høj | **Anbefalet til tool-use** |
| qwen2.5:14b | ~9 GB | ❌ For stor | Fremragende | Meget høj | Kræver 16GB |
| mistral:7b | ~4.1 GB | ✅ OK | God | Høj | Alternativ til qwen2.5:7b |
| phi3:mini | ~2.3 GB | ✅ Masser | Middel | Medium | Hurtig, billig |

**Anbefaling: `qwen2.5:7b` som primær Ollama-model**

Qwen2.5:7b er markant overlegen til structured output og function calling sammenlignet med Llama-familien i samme størrelsesklasse. Den passer komfortabelt i 8GB og efterlader 3GB headroom til OS og andre processer.

```bash
# Skift model på Hetzner
ollama pull qwen2.5:7b
ollama rm llama3.2:latest  # Frigiv 5GB

# Test function calling
ollama run qwen2.5:7b "Call a weather function for Copenhagen"
```

### Samlet LLM-strategi: Hvornår hvad?

```
Bruger sender besked
        │
        ▼
[Groq llama-3.3-70b-versatile]
        │
        ├─ Generelt svar (ingen tools): ✅ Brug Groq
        │
        ├─ Tool/function call nødvendig:
        │   ├─ Forsøg: Groq llama-3.1-8b-instant eller mixtral
        │   └─ Fallback: Anthropic claude-haiku (pålidelig tool-use)
        │
        ├─ Groq rate limit nået:
        │   └─ Fallback: Ollama qwen2.5:7b på Hetzner
        │
        └─ Groq API nede:
            └─ Fallback: Ollama qwen2.5:7b på Hetzner
```

**Konfigurations-princip:**
- Groq: Hurtige svar, generel konversation, lav latens
- Anthropic claude-haiku: Structured output, tool-use, JSON generation
- Ollama qwen2.5:7b: Offline fallback, privacy-sensitive requests, rate limit overflow

### Er Hetzner 8GB nok til Ollama + OpenClaw?

**Nuværende setup (Railway + Hetzner separat):** Ja, 8GB er rigeligt til kun Ollama.

**Hvis OpenClaw flyttes til Hetzner:** Snævert men muligt med qwen2.5:7b (4.7GB model + 1GB overhead = 5.7GB, efterlader 2.3GB til OS). Med llama3.2:8b (5GB model) er der meget lidt headroom.

**Anbefaling:** Behold llama3.2 erstattes af qwen2.5:7b, og behold OpenClaw på Railway (eller opgradér til Hetzner CX42 med 16GB ved flytning).

---

## 6. Hetzner server-vurdering

### Aktuel server: ubuntu-8gb-nbg1-1

```
Type:     CX32 (shared vCPU)
RAM:      8 GB
vCPU:     4 (shared)
Disk:     80 GB SSD
Location: Nuremberg (nbg1)
OS:       Ubuntu 22.04/24.04
Pris:     ~€9.49/måned
```

### "Shared vCPU" — hvad betyder det?

Hetzner's shared vCPU-instanser deler fysisk CPU-kapacitet med andre kunder. I praksis betyder det:
- **Burst-kapacitet**: God performance ved korte spikes
- **Sustained load**: Kan throttles hvis du konsistent bruger 100% CPU
- **Ollama inference**: Typisk bursty (høj CPU under generation, idle ellers) — godt match til shared vCPU

For Ollama-workloads er shared vCPU acceptabelt. Inference-hastighed på CPU er begrænset af RAM-båndbredde snarere end rå CPU-kraft.

### Memory-analyse: hvad kan køre?

**Scenarie 1: Kun Ollama (nuværende setup)**

```
OS + systemd:     ~500 MB
Ollama daemon:    ~200 MB
llama3.2 (Q4):   ~5.0 GB
Buffer:           ~2.3 GB
─────────────────────────
Total:            ~8.0 GB  ✅ Komfortabelt
```

**Scenarie 2: Ollama + OpenClaw på Hetzner**

```
OS + systemd:     ~500 MB
Ollama daemon:    ~200 MB
qwen2.5:7b (Q4): ~4.7 GB
OpenClaw (Node):  ~300 MB
Nginx:            ~50 MB
Buffer:           ~2.25 GB
─────────────────────────
Total:            ~8.0 GB  ✅ Muligt — snævert
```

**Scenarie 3: Ollama + OpenClaw + AI-CORE**

```
OS + systemd:     ~500 MB
Ollama daemon:    ~200 MB
qwen2.5:7b (Q4): ~4.7 GB
OpenClaw (Node):  ~300 MB
AI-CORE (Python): ~400 MB
Nginx:            ~50 MB
Buffer:           ~850 MB
─────────────────────────
Total:            ~7.0 GB  ⚠️ Meget snævert
```

### Serversammenligning: CX32 vs CX42

| Spec | CX32 (nuværende) | CX42 | CX52 |
|------|-----------------|------|------|
| RAM | 8 GB | 16 GB | 32 GB |
| vCPU | 4 shared | 8 shared | 16 shared |
| Disk | 80 GB | 160 GB | 240 GB |
| Pris | ~€9.49/md | ~€19.49/md | ~€38.49/md |
| Ollama model maks | qwen2.5:7b | qwen2.5:14b eller llama3.1:8b+tools | llama3.1:70b (Q4) |

**Anbefaling:**

- **Behold CX32** hvis OpenClaw forbliver på Railway og Hetzner kun kører Ollama
- **Opgrader til CX42** hvis du:
  - Flytter OpenClaw til Hetzner
  - Ønsker bedre Ollama-modeller (14B parametre)
  - Kører AI-CORE orchestrator på samme server
- **CX52** er overkill for nuværende use case

### Hvad kan flyttes til Hetzner?

**Stærkt anbefalet at flytte:**
- **OpenClaw gateway** — bedre kontrol over deploy, ingen rolling-deploy 409-problem, lavere latens til Ollama

**Kan flyttes:**
- **AI-CORE Python orchestrator** — lav memory footprint, naturlig co-location med Ollama

**Behold på Railway:**
- Intet kritisk — Railway's primære fordel er hurtig deploy fra Git, men det er ikke et krav

**Flytning af OpenClaw til Hetzner — quick guide:**

```bash
# 1. Installer Node.js på Hetzner
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. Installer openclaw
sudo npm install -g openclaw@2026.3.22

# 3. Opret systemd service
sudo nano /etc/systemd/system/openclaw.service
```

```ini
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/clawrunner
EnvironmentFile=/home/ubuntu/clawrunner/.env
ExecStart=/usr/bin/openclaw gateway run
Restart=on-failure
RestartSec=5
StartLimitInterval=60
StartLimitBurst=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 4. Start service
sudo systemctl enable --now openclaw
sudo systemctl status openclaw

# 5. Webhook via Nginx
sudo apt install -y nginx certbot python3-certbot-nginx
# Konfigurer nginx reverse proxy til port 3000 (eller OpenClaw's port)
```

---

## 7. Stabilitetstjekliste ✅

### Infrastructure

- [ ] **Webhook i stedet for polling** — eliminerer 409-problemet permanent. Se [sektion 4](#4-telegram-polling-vs-webhook) for guide
- [x] **Railway: `restartPolicyType = ON_FAILURE`** — er på plads
- [x] **Watchdog loop** — op til 20 genstarter med 5s delay, Telegram-notifikation ved genstart
- [ ] **openclaw opdateret til seneste version** — kørende `2026.3.22`, tilgængelig `2026.3.24`. Opdater og test
- [x] **`TELEGRAM_GROUP_ALLOW_FROM` sat explicit med bruger-ID** — på plads

### LLM & Models

- [ ] **Groq fallback model konfigureret** — ved function-call fejl skal `llama-3.1-8b-instant` eller `mixtral-8x7b` forsøges automatisk
- [ ] **Ollama model valgt der faktisk kører stabilt på 8GB** — erstat `llama3.2:latest` med `qwen2.5:7b` for bedre function calling
- [ ] **Model-test: function calling verificeret** — kør explicit test af tool-use på alle konfigurerede modeller inden produktionsdeploy

### Telegram

- [ ] **`deleteWebhook` kørt efter ENHVER redeploy** — tilføj til `railway-start.sh` som første kommando (eller bedre: skift til webhook og gør dette irrelevant)
- [ ] **Kun ÉN instans kører** — verificer med `getWebhookInfo` og Railway dashboard. Kig efter "pending_update_count" > 0 som tegn på akkumulerede beskeder fra nedetid
- [x] **Telegram-notifikation ved opstart** — er implementeret
- [x] **Telegram-notifikation ved genstart/watchdog** — er implementeret

### Monitoring

- [ ] **Railway log alerts sat op** — konfigurer alert ved ERROR-log pattern i Railway dashboard (Settings → Observability)
- [ ] **Cron-job der pinger botten hvert 10. minut** — notificerer via alternativ kanal (email/Discord webhook) hvis bot ikke svarer. Kan implementeres med GitHub Actions scheduled workflow eller Hetzner cron
- [ ] **HEARTBEAT.md med periodisk self-check task** — OpenClaw task der skriver heartbeat timestamp til fil/database hvert 5. minut; ekstern monitoring tjekker at timestamp er nyere end 10 minutter

### Deployment

- [ ] **Zero-downtime deploy strategi** — webhook eliminerer 409-problemet og er den anbefalede løsning
- [x] **Railway: ingen `healthcheckPath`** — fjernet efter Fejl 4, gateway eksponerer ikke `/`
- [ ] **CI: automatisk test af bot response før deploy godkendes** — GitHub Action der sender testbesked til bot og verificerer svar inden Railway deploy godkendes

---

## 8. Anbefalet målarkitektur

### Nuværende arkitektur (problematisk)

```
[Telegram]
    │
    │  long-polling (problematisk!)
    │
    ▼
[Railway: OpenClaw gateway]
    │                    │
    │                    │
    ▼                    ▼
[Groq API]    [Hetzner: Ollama llama3.2]
                         │
                         ▼
              [AI-CORE: Python orchestrator]
```

**Problemer:**
- Long-polling = 409-risiko ved deploy
- OpenClaw på Railway = ingen kontrol over deploy-overlap
- Groq function calling = ustabil for tool-use

### Målarkitektur A: Webhook på Railway (minimal ændring, maksimal stabilitet)

```
[Telegram]
    │
    │  HTTPS POST webhook (stabilt!)
    │
    ▼
[Railway: OpenClaw gateway]          [Groq API: generelle svar]
    │         │                           ▲
    │         └───────────────────────────┘
    │
    │  HTTP (intern)
    │
    ▼
[Hetzner VPS: ubuntu-8gb-nbg1-1]
    │
    ├── [Ollama: qwen2.5:7b]     ← fallback LLM + tool-use
    │       (port 11434)
    │
    └── [AI-CORE: Python orchestrator]
            (port 8000)
```

**Deployment flow (webhook, ingen 409):**
```
git push → Railway build → ny container starter → webhook URL aktiv →
Railway retter traffic → gammel container stoppes → ingen overlap-konflikt
```

### Målarkitektur B: Alt på Hetzner (maksimal kontrol)

```
[Telegram]
    │
    │  HTTPS POST webhook
    │
    ▼
[Hetzner VPS: CX42 — 16GB anbefalet]
    │
    ├── [Nginx reverse proxy: :443 → :3000]
    │       (TLS via Let's Encrypt)
    │
    ├── [OpenClaw gateway: port 3000]
    │       (systemd managed)
    │
    ├── [Ollama: qwen2.5:7b]
    │       (port 11434, localhost only)
    │
    └── [AI-CORE: Python orchestrator]
            (port 8000, localhost only)

[Groq API] ←── OpenClaw (udgående, primær LLM)
[Anthropic API] ←── OpenClaw (udgående, structured output fallback)
```

**Fordele ved Arkitektur B:**
- Ingen rolling deploy overlap
- Lavere latens mellem OpenClaw og Ollama (localhost vs. internet)
- Fuld kontrol over genstart og deployment
- Lavere månedlig udgift (€9-19 Hetzner vs. $5+ Railway)

**Ulemper:**
- Mere administration (nginx, certbot, systemd)
- Manuel deploy-process (kan automatiseres med GitHub Actions + rsync/ssh)

### Anbefalet vej fremad

```
Nu → Arkitektur A (skift polling→webhook, bliv på Railway)
      ↓ (om 1-2 måneder, hvis stabilitet er ønsket)
    Arkitektur B (flyt til Hetzner CX42, fuld kontrol)
```

---

## 9. Hurtige wins (kan gøres i dag)

Disse fem handlinger giver størst stabilitetsforbedring for mindst indsats. De er listet i prioriteret rækkefølge.

---

### 1. Kør `deleteWebhook` inden ENHVER genstart (5 minutter)

Dette er en **akut fix** der skal gøres **nu** og ved enhver fremtidig redeploy indtil webhook er implementeret. Uden dette vil Fejl 3 gentage sig.

**Tilføj til starten af `scripts/railway-start.sh`:**

```bash
#!/bin/bash
set -e

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Clearing Telegram state before startup..."
RESULT=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true")
echo "deleteWebhook result: ${RESULT}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting OpenClaw gateway..."
exec openclaw gateway run
```

**Test:**
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
# Forventet: "url": "", "pending_update_count": 0
```

---

### 2. Opdater openclaw til 2026.3.24 (10 minutter)

Version `2026.3.24` er tilgængelig og indeholder sandsynligvis bugfixes for Fejl 7 (respawn crash).

```bash
# Ret package.json
{
  "dependencies": {
    "openclaw": "2026.3.24"
  }
}
```

```bash
# Lokalt test efter opdatering
npm install
openclaw gateway run --config openclaw.json
# Verificer at bot svarer i Telegram inden Railway push
git add package.json package-lock.json
git commit -m "chore: upgrade openclaw to 2026.3.24"
git push
```

---

### 3. Erstat llama3.2 med qwen2.5:7b på Hetzner (15 minutter)

Forbedrer function calling markant og frigiver marginal RAM.

```bash
# SSH til Hetzner
ssh root@178.104.83.125

# Pull ny model (kører i baggrunden, ~4.7GB download)
ollama pull qwen2.5:7b

# Opdater OLLAMA_MODEL env var i Railway (eller openclaw.json)
# Railway Dashboard → Variables → OLLAMA_MODEL = qwen2.5:7b

# Test
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Call a function to get weather in Copenhagen",
  "stream": false
}' | jq .response

# Fjern gammel model (frigiver ~5GB)
ollama rm llama3.2:latest
```

---

### 4. Implementer ekstern ping-monitoring via GitHub Actions (20 minutter)

Fejl 6 (silent polling drop) var udetektet i ~1 time. En simpel GitHub Actions workflow kan pinge botten hvert 10. minut og sende en Telegram-alarm ved manglende svar.

**Opret `.github/workflows/bot-healthcheck.yml` i dit repo:**

```yaml
name: Bot Healthcheck

on:
  schedule:
    - cron: '*/10 * * * *'  # Hvert 10. minut
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Send ping to bot
        run: |
          # Send /ping kommando til bot via Telegram API
          curl -s -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
            -d "chat_id=${{ secrets.TELEGRAM_ADMIN_CHAT_ID }}" \
            -d "text=/ping" \
            -d "disable_notification=true"

      - name: Wait for response
        run: sleep 30

      - name: Check for pong response
        run: |
          # Hent seneste updates og tjek for 'pong' svar inden for de sidste 60 sekunder
          UPDATES=$(curl -s "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/getUpdates?limit=5")
          RECENT_PONG=$(echo $UPDATES | python3 -c "
          import sys, json, time
          data = json.load(sys.stdin)
          now = time.time()
          for u in data.get('result', []):
              msg = u.get('message', {})
              if msg.get('date', 0) > now - 60 and 'pong' in msg.get('text', '').lower():
                  print('PONG RECEIVED')
                  sys.exit(0)
          print('NO PONG')
          sys.exit(1)
          ")
          echo $RECENT_PONG

      - name: Alert if bot is down
        if: failure()
        run: |
          curl -s -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
            -d "chat_id=${{ secrets.TELEGRAM_ADMIN_CHAT_ID }}" \
            -d "text=⚠️ BOT HEALTHCHECK FEJLEDE — bot svarer ikke på /ping. Tjek Railway logs." \
            -d "parse_mode=HTML"
```

**GitHub Secrets der skal sættes:**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_CHAT_ID` (din personlige chat ID)

---

### 5. Skift til Telegram webhook (1-2 timer — permanent fix på Fejl 3)

Dette er den vigtigste enkeltændring. Den eliminerer Fejl 3 (409 Conflict) permanent og gør deployment markant mere robust.

**Trin-for-trin:**

```bash
# TRIN 1: Find Railway public URL
# Railway Dashboard → din service → Settings → Domains
# Kopier URL, fx: https://clawrunner-production.railway.app

# TRIN 2: Sæt webhook
export BOT_TOKEN="din_bot_token"
export RAILWAY_URL="https://clawrunner-production.railway.app"

curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=${RAILWAY_URL}/telegram/webhook" \
  -d "max_connections=1" \
  -d "allowed_updates=[\"message\",\"callback_query\"]" | jq .

# TRIN 3: Verificer
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | jq .
# Tjek: "url" er sat, "last_error_message" er tom

# TRIN 4: Opdater openclaw.json
# Sæt telegram.mode = "webhook" og konfigurer webhookPath

# TRIN 5: Redeploy
git add openclaw.json
git commit -m "feat: switch telegram to webhook mode"
git push
```

**Verificering efter deploy:**
```bash
# Send en testbesked til botten i Telegram
# Tjek Railway logs for:
# "Telegram webhook received" eller tilsvarende
# Svar bør komme inden for 2 sekunder
```

---

## Appendiks A: Nyttige kommandoer

```bash
# Tjek bot-status
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# Tjek webhook-status
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | jq .

# Slet webhook og ryd pending updates
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"

# Tjek Ollama-status på Hetzner
ssh root@178.104.83.125 "ollama list && systemctl status ollama"

# Tjek Railway deployment-logs
railway logs --tail 100

# Force redeploy på Railway
railway redeploy
```

## Appendiks B: Fejlfinding 409-fejl

Hvis botten er fast i 409-backoff-loop:

```bash
# 1. Identificer problemet
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
# Hvis url er tom og bot ikke svarer = polling-konflikt

# 2. Ryd Telegram state
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"

# 3. Force redeploy på Railway
railway redeploy --detach

# 4. Overvåg opstart
railway logs -f
# Vent på "OpenClaw gateway started" eller tilsvarende

# 5. Verificer bot svarer
# Send /start i Telegram — bør svare inden for 5 sekunder
```

---

*Rapport udarbejdet: 2026-03-28 · OpenClaw 2026.3.22 · Railway Hobby · Hetzner CX32*
