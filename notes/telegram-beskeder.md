# Telegram-beskeder — hvad du får og hvordan du styrer det

Det er **Telegram-beskederne** du får fra OpenClaw og NFT-arbitrage. Her er hvad der sender, og hvordan du slår det ned eller tilpasser.

---

## 0. Intake — systemet fanger hvad der skal ske

**Hver gang du poster noget i Telegram** (eller anden kanal) skal agenten **altid** tilføje en post i:

- **`workspace/intake/telegram/YYYY-MM-DD.md`**

Med din besked (raw) + **HVAD SKAL SKE** (udtrukne opgaver, beslutninger, idéer). Det står i **workspace/AGENTS.md** som påbud. Så kan CHECKLIST, cron og memory bruge det bagefter. Se `workspace/intake/README.md` for format.

---

## 1. OpenClaw (gateway + cron)

Når cron-jobs kører (Build Conductor, Investor Scout, Status Weaver), kan gatewayen sende **opsummeringer til Telegram** via `delivery.mode: "announce"` og `channel: "last"` — dvs. resultatet af den seneste agent-kørsel kan blive annonceret i din kanal.

- **Konfiguration:** I `cron/jobs.json` har hvert job en `delivery`-sektion. Hvis du vil **færre** beskeder: du kan ændre eller fjerne delivery, eller slå cron-jobs ned (se OpenClaw docs for cron delivery).
- **Hvor:** Jobs er defineret i `cron/jobs.json`; gatewayen læser ved start.

---

## 2. NFT-arbitrage (trading-notifikationer)

Backend sender beskeder via **TelegramNotifier** til den chat_id der står i config. Beskeder typer:

| Type | Hvad | Slå fra / til |
|------|------|----------------|
| **Trade executed** | Hver fuld køb+salg | `notifications.telegram.notify_on_trade: false` |
| **Opportunity** | Høj-konfidens muligheder (til manuel review) | `notify_on_opportunity: false` |
| **Error** | Kritiske fejl | `notify_on_error: false` |
| **Daily summary** | Daglig P&L-rapport | `notify_on_daily_summary: false` |
| **Trend shift** | Når trend ændrer sig markant | `notify_on_trend_shift: false` |
| **Risk warning** | Når risikogrænser nærmes | `notify_on_risk_warning: false` |
| **Parameter change** | Når auto-tuner ændrer parametre | `notify_on_parameter_change: false` |
| **Startup** | Én besked når backend starter | Kræver kode-ændring for at slå fra |

**Konfiguration:**  
`workspace/projects/nft-arbitrage/config/settings.yaml` → sektionen `notifications.telegram`:

```yaml
notifications:
  telegram:
    enabled: true
    notify_on_opportunity: true
    notify_on_trade: true
    notify_on_error: true
    notify_on_daily_summary: true
    notify_on_trend_shift: true
    notify_on_risk_warning: true
    notify_on_parameter_change: true
```

Sæt den relevante `notify_on_*` til `false` for at stoppe den type beskeder. Genstart NFT-arbitrage backend efter ændring.

---

## 3. Én sti til “det er Telegram jeg får”

- **OpenClaw-cron:** Beskeder = resultat af agent-jobs (build, investor, status). Styr via cron-job config og delivery.
- **NFT-arbitrage:** Beskeder = trades, opportunities, fejl, daglig opsummering, trend, risk, parameter-ændringer. Styr via `settings.yaml` under `notifications.telegram`.

Hvis du vil have **færre** beskeder: start med at slå `notify_on_opportunity` og evt. `notify_on_trend_shift` / `notify_on_parameter_change` fra i NFT-arbitrage, og tjek cron delivery i OpenClaw hvis det er der det brænder.
