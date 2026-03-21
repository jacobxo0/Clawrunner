# Debug Telegram – brug denne note til at fikse problemet

**Formål:** Når brugeren har sendt en besked via Telegram og botten svarer ikke / intake bliver ikke skrevet, brug denne note og udfør fix uden at spørge.

---

## 1. Hvad der blev fundet (2026-03-08)

- **getWebhookInfo** (Telegram API): `url` var **tom** (`""`). Det betyder at Telegram **ikke sender** brugerens beskeder til nogen server – så gatewayen modtager aldrig beskeden, og der skrives ingen intake i `workspace/intake/telegram/YYYY-MM-DD.md`.
- **Preflight:** Config OK, Ollama tilgængelig, gateway port 18789 åben, Telegram getMe OK (bot: Jnkri_claw_bot). Problemet er alene manglende webhook-URL.

**Fix udført samme dag:** Webhook er sat til `https://clawrunner-production.up.railway.app/telegram`. Telegram sender nu beskeder til Railway. Send en ny testbesked til botten – den skal nu nå gatewayen på Railway. Hvis Railway-gatewayen kører og er konfigureret med samme workspace/intake-path, bør intake blive skrevet (tjek på den maskine hvor Railway deploy kører, eller hvor workspace synkroniseres).

---

## 2. Prompt til agent-systemet (brug disse ord)

> **Opgave: Fix Telegram så beskeder når gatewayen og intake skrives.**  
> Root cause er at Telegram-webhook ikke er sat (getWebhookInfo viser tom url).  
> 1) Hent webhook-status: kør `.\scripts\get-telegram-webhook-info.ps1` eller `Invoke-RestMethod "https://api.telegram.org/bot<token>/getWebhookInfo"` (token fra openclaw.json channels.telegram.botToken).  
> 2) Hvis url er tom: sæt webhook til **produktion** med `.\scripts\set-telegram-webhook.ps1 -Url "https://clawrunner-production.up.railway.app"` (så Telegram sender til Railway), ELLER til **lokal** med ngrok: start `ngrok http 18789`, kopier https-URL, kør `.\scripts\set-telegram-webhook.ps1 -Url "https://<din-ngrok-url>"`.  
> 3) Efter sætning: verificer med getWebhookInfo at url er ikke-tom. Send derefter en testbesked til botten og tjek at `workspace/intake/telegram/YYYY-MM-DD.md` (dagens dato) får en ny post med raw besked + HVAD SKAL SKE.  
> 4) Hvis intake stadig ikke skrives: tjek at gatewayen på den valgte URL (Railway eller ngrok) kører og at den skriver til workspace-intake; tjek gateway-logs for fejl ved modtagelse af /telegram.  
> Kør alle kommandoer selv; involvér brugeren kun ved manglende credentials eller valg mellem Railway vs. kun lokal.

---

## 3. Kommandoer (kør selv)

```powershell
# Webhook-status
.\scripts\get-telegram-webhook-info.ps1

# Sæt webhook til Railway (produktion)
.\scripts\set-telegram-webhook.ps1 -Url "https://clawrunner-production.up.railway.app"

# Sæt webhook til lokal (efter ngrok http 18789)
.\scripts\set-telegram-webhook.ps1 -Url "https://XXXX.ngrok-free.app"

# Efter fix: tjek intake
Get-Content "workspace\intake\telegram\$(Get-Date -Format 'yyyy-MM-dd').md" -Tail 30
```

---

## 4. Reference

- RUNBOOK.md § "Telegram svarer ikke" (webhook, ngrok, set-telegram-webhook).
- notes/telegram-svarer-ikke-lokal.md
- workspace/intake/telegram/README.md (format for intake-poster)
