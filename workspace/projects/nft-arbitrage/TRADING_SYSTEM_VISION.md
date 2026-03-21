# NFT Arbitrage → Super hyper aktivt, selvforbedrende, ikke-tabende trading-system

**Formål:** At dette projekt ikke er “bare” en bot, men et **system der konstant scanner, kun handler når edge er reel, og lærer af hver trade** så det over tid bliver strengere og mere profitabelt.

---

## De tre søjler

### 1. Super hyper aktivt
- **Scanner kører ofte:** Listings, bids, sales indlæses kontinuerligt eller med kort interval (minutvis), så muligheder ikke forsvinder før vi ser dem.
- **Flere strategier parallelt:** Bid-spread, stale listing, trait mispricing, cross-marketplace kører samtidig; opportunity engine vælger det bedste pr. situation.
- **Hurtig beslutning:** QC-agent + cost engine giver go/no-go hurtigt; execution layer er klar (speed_executor, stream_sniper).
- **I praksis:** `scan_worker`, `ingestion_worker`, `stream_sniper` + scheduler/cron med korte intervaller. Redis cache til bids/floors så vi ikke spørger APIs unødvendigt.

### 2. Selvforbedrende
- **Parameter Tuner** (`src/agents/parameter_tuner.py`): Justerer min. ROI, confidence-thresholds og strategivægte ud fra faktisk hit rate. For mange tab → strammere krav. For mange missede muligheder → lidt løsere (inden for safe bounds).
- **Meta-Learning Agent** (`src/agents/meta_learning.py`): Ugentlig AI-gennemgang af alle trades og opportunities. Finder mønstre (fx “bid_spread virker i collection X, trait_mispricing ikke”), foreslår ændringer i config/strategier; høj konfidens kan auto-applies.
- **Code evolution (arkitekturdoc):** Code reviewer + bug fixer der forbedrer selve koden ud fra logs og fejl.
- **Feedback-sløjfen:** PnL og outcome → trades-tabel → Parameter Tuner + Meta-Learning → opdateret config/strategivægte → næste runde handler med bedre parametre.

### 3. Ikke-tabende (risikostyring)
- **Kun handle når net_profit er reelt:** Cost engine trækker altid fees, royalties, gas, risk buffer. Ingen trade uden at `net_profit > min_threshold` (config).
- **QC / Guardrails:** QC-agent tjekker at bid/listing stadig findes, at collection risk er under threshold, at exposure ikke er for høj. APPROVE / REJECT / HUMAN_REVIEW.
- **Risk Engine:** Wash-trade score, likviditet, volumen pr. collection. Ingen execution hvis collection er for risikabel.
- **Portfolio/Risk Manager:** Max eksponering pr. collection, max åbent inventory, max dagligt tab, position sizing. Stop efter N konsekutive tab (fx 3).
- **Semi-auto først:** MVP med human-in-the-loop (approve tickets) så systemet lærer uden at brænde kapital; fuld auto kun når hit rate og regler er dokumenteret.

---

## Hvordan det hænger sammen

```
[Data: listings, bids, sales] → Ingest → Normaliser
        ↓
[Cost engine] → net_profit, ROI, confidence pr. mulighed
        ↓
[Opportunity Engine] → strategi-plugins (bid_spread, stale, trait, cross-market)
        ↓
[QC Agent] → APPROVE / REJECT / HUMAN_REVIEW
        ↓
[Decision Engine] → risk level, auto vs notify
        ↓
[Executor] → køb → (accept bid / relist) → sell
        ↓
[Trades + Opportunities logget] → Parameter Tuner + Meta-Learning → justerer parametre → næste scan
```

Alt er allerede skitseret i arkitekturen og delvist implementeret i `src/`. Målet er at **få sløjfen til at køre** og derefter stramme den op, så “ikke-tabende” bliver reelt (stigende hit rate, faldende unødvendige trades).

---

## Konkret næste skridt (så det ikke er meningsløst)

1. **Få pipeline til at køre regelmæssigt**
   - Sørg for at `scheduler` / cron kører: scan_worker, ingestion_worker med kort interval (fx hvert 1–5 min for scan).
   - Evt. OpenClaw-cron job der kalder dit NFT-arbitrage API eller en `scripts/run_scan.py`, så hele OpenClaw-rammen driver scanningen.

2. **Tydelige “ikke-tabende”-regler**
   - `min_net_profit_eth` og `min_confidence` i config – ingen trade under disse.
   - Stop efter N konsekutive tab (fx 3): deaktivér auto eller kræv human review indtil gennemgang.
   - Max dagligt tab / max exposure pr. collection (portfolio_manager) – hårdt hængt på.

3. **Selvforbedring aktiv**
   - Parameter Tuner kører dagligt (eller efter hver N trades).
   - Meta-Learning kører ugentligt; output (anbefalinger) gemmes eller sendes til Slack/Telegram, så du ser at systemet “tænker”.

4. **Synlighed**
   - Dashboard/API: vis opportunities (pending/approved/rejected), trades, PnL, og seneste tuning/meta-learning anbefalinger.
   - OpenClaw: Notion/Slack/Telegram kan bruges til alerts og opsummeringer, så “integrationerne” giver mening i forhold til dette system.

---

## Næste skridt (konkret)

| # | Handling | Status |
|---|----------|--------|
| 1 | **Start pipeline:** Kør backend (FastAPI + scheduler). Ingestion hver 10s, scan hver 15s, risk 15 min, parameter tuner dagligt, meta-learning mandag 09:00. | Scheduler findes i `src/workers/scheduler.py` – start appen. |
| 2 | **Ikke-tabende:** `config/settings.yaml` har allerede `cost_engine.min_net_profit_eth`, `risk.max_daily_loss_eth`, `risk.stop_loss_pct`. Evt. tilføj `risk.consecutive_loss_limit: 3` og brug det i scan_worker/executor til at stoppe auto efter N tab i træk. | Config har risk; consecutive-loss gate kan tilføjes. |
| 3 | **OpenClaw:** Cron-job eller script der enten (a) pinger NFT-arbitrage health-endpoint, eller (b) kalder en run_scan-endpoint. Telegram/Slack til alerts (opportunities, trades, daily summary). | Integrationer (Telegram/Slack/Notion) giver mening her: alerts og rapporter. |
| 4 | **Synlighed:** Brug dashboard/API til at se opportunities, trades, PnL. Meta-learning og parameter tuner skriver anbefalinger – få dem vist eller sendt til dig. | Dashboard/API findes; tilkobl notifikationer. |

Uden at starte backend og få sløjfen til at køre, føles resten meningsløst. Første skridt: **kør NFT-arbitrage appen** (docker-compose eller `uvicorn` mod `src.main`) så scheduler kører.

---

## Kort sagt

- **Hyper aktivt** = korte scan-intervaller, flere strategier, hurtig QC og execution.
- **Selvforbedrende** = Parameter Tuner + Meta-Learning + (valgfrit) code-evolution, der konstant trækker læring fra PnL og outcomes.
- **Ikke-tabende** = strenge gates (cost engine, QC, risk engine, portfolio limits, stop-after-losses), semi-auto indtil tallene er gode nok.

Når det kører i loop, er NFT-arbitrage ikke “bare en bot” – det er et **trading-system der skruer sig selv op mod højere aktivitet og lavere tab**.
