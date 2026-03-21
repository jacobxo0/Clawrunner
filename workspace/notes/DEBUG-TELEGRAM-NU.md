# Debug Telegram – brug denne note til at fikse problemet

## ⚠️ VIGTIGT — LÆS DETTE FØRST

**Clawrunner på Railway bruger POLLING-mode, IKKE webhook.**

- Gateway kører som WebSocket (port 18789) og bruger `getUpdates` (polling)
- Der er INGEN `/telegram` HTTP endpoint — webhook vil give 502
- **MÅ IKKE sætte webhook til Railway URL** — det bryder polling og botten dør

**Korrekt tilstand:** `getWebhookInfo` skal returnere `url: ""`
**Hvis url ikke er tom:** Kald deleteWebhook med det samme.

```
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook?drop_pending_updates=true"
```

---

## Hvad gør du hvis botten ikke svarer?

1. **Tjek webhook er tom:**
   Kald Telegram API getWebhookInfo. Skal vise url som tom streng.
   Hvis ikke tom — slet webhook straks.

2. **Tjek Railway er Online:**
   Clawrunner skal være grøn i Railway dashboard.

3. **409-fejl i logs = webhook er sat.**
   Slet webhook. Botten starter automatisk polling igen inden for 30s.

---

## Hvad du ALDRIG må gøre

- ALDRIG sæt webhook til clawrunner-production.up.railway.app/telegram
- ALDRIG sæt webhook mens Railway kører polling
- ALDRIG kør polling OG webhook samtidig på samme token

---

## Reference

- Telegram polling virker når: webhook er tom + Clawrunner er Online på Railway
