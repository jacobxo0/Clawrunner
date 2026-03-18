# Clawrunner — Debug Status

## Hvad er dette projekt
OpenClaw gateway deployet på Railway. Formål: Telegram-bot der svarer via Groq AI.

## Nuværende status: Gateway crasher ved opstart

### Symptom
`npx openclaw gateway run` eksporterer med kode 1 umiddelbart efter:
```
Registered plugin command: /pair (plugin: device-pair)
[EXIT] Gateway exited with code 1
```

### Hvad vi har fundet

**Crash-lokation (fra `--trace-exit`):**
```
at file:///app/node_modules/openclaw/dist/entry.js:372:14
```

Koden der kører der:
```js
process$1.exitCode = 1;
console.error("[openclaw] Failed to respawn CLI:", error ...);
// ...
process$1.exit(1);
```

OpenClaw forsøger at **respawne CLI-processen** og fejler. Det er ikke en konfigurationsfejl — det er en intern mekanisme i OpenClaw der crasher.

**`openclaw doctor` opfører sig identisk:**
- Printer kun banner + `┌  OpenClaw doctor`
- Eksiterer med kode 1 uden at køre nogen checks
- Samme crash-lokation (entry.js:372)

### Hvad vi har udelukket
- ✅ Alle API-nøgler er sat: `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`, `BRAVE_API_KEY`
- ✅ Config genereres korrekt fra template
- ✅ Config kopieres til `/root/.openclaw/openclaw.json` (korrekt HOME)
- ✅ `gateway.bind`, `models.providers` schema-fejl er fikset
- ✅ Korrekt subkommando: `gateway run` (ikke bare `gateway`)
- ✅ Telegram, GitHub skill, Notion skill — ingen af dem er årsagen
- ✅ Groq vs. Anthropic model — ingen forskel

### Root cause (formodning)
OpenClaw 2026.3.13 forsøger at **respawne sin egen CLI-proces** som en child-process, og denne mekanisme fejler i Railway's container-miljø (formentlig pga. process-isolation, manglende TTY, eller fordi `npx` ikke kan genfindes fra child-processen).

## Konfiguration der er klar til brug

Alle disse er fixet og klar:
- `openclaw.railway.example.json` — valid config, ingen schema-fejl
- `scripts/build-config.js` — substituerer env-vars korrekt
- `scripts/railway-start.sh` — bygger og kopierer config korrekt
- `railway.toml` — `startCommand = "bash scripts/railway-start.sh"`
- `Dockerfile` — `node:22-bookworm-slim`, `npm install`

## Næste skridt (afventer instruks)

Mulige veje frem:
1. **Pin en ældre OpenClaw version** i `package.json` der ikke bruger respawn-mekanismen
2. **Kontakt OpenClaw support** med fejlen (entry.js:372, respawn failure i container)
3. **Brug `npm start` direkte** (package.json har `"start": "openclaw gateway --port ${PORT:-18789}"`) — den ældre kommando uden `run` subkommand
4. **Skift til en anden gateway-løsning** der ikke kræver OpenClaw
