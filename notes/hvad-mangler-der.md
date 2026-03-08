# Hvad mangler der

Kort oversigt over det der stadig er **åbent**, **blokeret** eller **todo** i OpenClaw og tilknyttede projekter. Opdateres ved behov.

---

## Blokerende

| Hvad | Hvorfor det mangler | Løsning |
|------|---------------------|--------|
| **Fuld commodity research GO/NO-GO** | Live web research kræver Brave Search API | Sæt nøgle: `openclaw configure --section web` eller `apiKey` i `openclaw.json` under `tools.web.search`, eller `BRAVE_API_KEY` hvor gateway kører. Se `notes/brave-search-api.md`. |

---

## I gang / partial

| Område | Hvad mangler |
|--------|----------------|
| **Deps** | Tjek at alle pakker er installeret i root-venv: kør `.\install-deps-batched.ps1` fra OpenClaw-roden. |
| **Wallet-autopilot** | Wallet-monitor (gas/spread, PnL, logformat) under udvikling i nft-arbitrage; cron-job når script er klar. |
| **Dashboard** | Statisk dashboard findes; Vite+Tailwind-app med kanban/metrics fra statusfiler under opbygning. |
| **Status-board** | instant-mesh har logs/status; samlet view på tværs af projekter mangler. |
| **Commodity-rapport** | Baseline kan udfyldes nu; sektioner 2.1–2.4, 4 og 5 med **kilder** afventer Brave API + web research. |

---

## Todo (ikke startet)

| Task | Note |
|------|------|
| **Auto-summaries i chat** | Afhænger af cron + delivery (announce); Telegram/cron allerede grønt. |
| **Agent templates** | `agents/templates/` kan tilføjes; CORE-F + hacks er beskrevet i notes. |
| **Reklamefilms-generator** | Nyt projekt: brief → storyboard/script/shotliste. |
| **Trading Status Agent som cron-job** | Agent + run-script findes; kan tilføjes til `cron/jobs.json` (eller via `openclaw cron add`) for daglig status. |
| **WFGY 16-problem reference** | Kort reference til RAG/agent-debug (link + modes) kan tilføjes under notes hvis du vil bruge det ved fejldiagnose. |

---

## Færdigt (reference)

- Pip batchers, fælles .venv, RUNBOOK, PYTHON, cron jobs (3 stk), agent-prompts (Build/Investor/Status + Trading Status), CORE-F, dashboard (statisk), checkliste, START-HER, observation loop + forecast gate + decision knowledge (NFT), mobil-interface (/mobile), Telegram-dokumentation, Brave config-struktur + doc, commodity rapport-skabelon + research-plan.

---

**Næste konkrete skridt (hvis du vil lukke huller):**

1. **Brave API:** Sæt nøgle → genstart gateway → kør web research og udfyld commodity-rapporten med kilder.
2. **Gateway:** Genstart hvis du har ændret cron/config, så jobs og tools (web search) er aktive.
3. **Telegram:** Slå evt. nogle notifikationstyper ned i `workspace/projects/nft-arbitrage/config/settings.yaml` under `notifications.telegram` hvis du får for mange beskeder (se `notes/telegram-beskeder.md`).
