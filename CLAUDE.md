# Clawrunner — Status

## Hvad er dette projekt
OpenClaw gateway deployet på Railway. Formål: Telegram-bot der svarer via Groq AI.
Live URL: **https://clawrunner-production.up.railway.app**

## Nuværende status: KØRER

Gateway er oppe og svarer på `clawrunner-production.up.railway.app` (HTTP 200, Control UI tilgængeligt).

### Løste problemer

| Problem | Fix | Commit |
|---------|-----|--------|
| OpenClaw respawn-crash i Railway container | `OPENCLAW_NO_RESPAWN=1` + upgrade til 2026.5.6 | a2e602c |
| `device-pair` plugin crash | Disabled i config | d812e81 |
| Telegram 409 Conflict (polling overlap) | Skiftet til **webhook mode** via `RAILWAY_PUBLIC_DOMAIN` | seneste |
| `gateway.bind` loopback-default | Sat til `lan` | 8872289 |
| Brave search ikke bundled | Disabled | 438db17 |

### Telegram webhook mode (aktiv)

`railway-start.sh` auto-konstruerer webhook URL fra `RAILWAY_PUBLIC_DOMAIN` (sættes automatisk af Railway):
```
TELEGRAM_WEBHOOK_URL=https://clawrunner-production.up.railway.app/telegram-webhook
```

OpenClaw lytter på `/telegram-webhook` og kalder `setWebhook` automatisk ved opstart.
Start-scriptet registrerer webhook med Telegram inden gateway starter.

## Konfiguration

- `openclaw.railway.example.json` — config-template med env-var-placeholders
- `scripts/build-config.js` — substituerer env-vars ind i template
- `scripts/railway-start.sh` — bygger config, registrerer Telegram webhook, starter gateway
- `railway.toml` — `startCommand = "bash scripts/railway-start.sh"`
- `Dockerfile` — `node:22-bookworm-slim`

## Railway Variables der skal sættes

| Variabel | Påkrævet | Note |
|----------|----------|------|
| `OPENCLAW_GATEWAY_TOKEN` | Ja | Gateway auth-token |
| `TELEGRAM_BOT_TOKEN` | Ja | Telegram bot-token fra BotFather |
| `GROQ_API_KEY` | Ja | Groq API-nøgle |
| `TELEGRAM_WEBHOOK_URL` | Nej | Auto-sat fra RAILWAY_PUBLIC_DOMAIN |
| `BRAVE_API_KEY` | Nej | Disabled i config |

## Genstart / redeploy

```bash
# Force redeploy (via Railway CLI)
railway redeploy

# Check logs
railway logs --tail 100
```

## Potentielle forbedringer

1. **Ekstern monitoring** — GitHub Actions workflow der pinger botten hvert 10. minut (se docs/DEPLOYMENT_ANALYSIS.md sektion 9)
2. **Fallback model** — Groq llama-3.1-8b-instant til function calling (llama-3.3-70b er ustabil til tool-use)
3. **Hetzner migration** — Fuld kontrol, ingen rolling-deploy overlap (se docs/DEPLOYMENT_ANALYSIS.md)
