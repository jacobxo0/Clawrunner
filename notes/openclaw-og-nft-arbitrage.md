# OpenClaw og NFT Arbitrage — hvad du kan bruge herfra

NFT-arbitrage live i `workspace/projects/nft-arbitrage`. Her er hvad der **allerede er i gang** i OpenClaw-projektet og hvordan det kan bruges til trading-systemet.

---

## 1. Cron + gateway

- **Gateway** læser `cron/jobs.json` og kører agent-jobs på plan (Build Conductor 08:00, Investor Scout man/ons 10:00, Status Weaver 20:00).
- **Brug til NFT arbitrage:** Du kan tilføje et **cron-job** der kører en **Trading Status Agent** (fx dagligt): den læser trading vision, observation/forecast-docs og evt. output fra `workspace/projects/nft-arbitrage/scripts/` (check_pnl, check_today, check_db_state) og poster en kort status eller opdaterer en status-fil.
- Se `cron/README.md` og `cron/CRON-SETUP.md`. Job-ids er **UUID** (brug `openclaw cron list` efter tilføjelse).

---

## 2. Agenter og prompts

| Agent | Placering | Brug til NFT arbitrage |
|-------|------------|-------------------------|
| **Build Conductor** | `workspace/agents/instant-mesh/BUILD_CONDUCTOR.md` | Instant Mesh; ikke direkte NFT. |
| **Investor Scout** | `workspace/agents/instant-mesh/INVESTOR_SCOUT.md` | Investor-fokus; kan evt. inkludere “trading PnL / funding need” i rapport. |
| **Status Weaver** | `workspace/agents/instant-mesh/STATUS_WEAVER.md` | Opsummerer build-log, investor, wallet. **Kan udvides** til også at læse en `nft-arbitrage-status.md` eller trading-log, så status-board viser både Instant Mesh og trading. |
| **Research Agent** | `workspace/agents/RESEARCH_AGENT.md` | **Direkte brug:** Før du tilføjer nye collections eller strategier, kør Research Agent med brief (fx “NFT collection X, liquidity, wash risk”) → GO/NO-GO og kilder. |
| **Profit Validator** | `workspace/agents/PROFIT_VALIDATOR.md` | **Direkte brug:** Nye ideer (fx “trait mispricing på chain Y”) → Profit Validator med idea brief → GO/NO-GO, cost model, krav til build. |
| **Trading Status Agent** | `workspace/agents/TRADING_STATUS_AGENT.md` (ny) | Læser trading vision, observation loop, forecast gate; evt. kører check-scripts; laver kort status til chat eller status-board. |

---

## 3. CORE-F og agent-system

- **CORE-F** (Comprehend → Orchestrate → Respond → Evaluate → Fine-tune) står i `notes/agent-system.md`.
- **Til trading:** Observation loop = løbende **Comprehend**; forecast gate = **Evaluate**; parameter tuner + meta-learning = **Fine-tune**. Du behøver ikke ændre kode for det — det er en måde at beskrive og logge faser på (fx i en trading-log som Status Weaver kan læse).

---

## 4. Scripts og run-scripts

- **OpenClaw-rod:** `scripts/start-gateway.ps1`, `scripts/do-something-now.ps1`, `scripts/setup-python-env.cmd`.
- **Workspace:** `workspace/scripts/run_build_conductor.ps1`, `run_investor_scout.ps1`, `run_status_weaver.ps1`, `run_research_agent.ps1`.
- **NFT-arbitrage:** `workspace/projects/nft-arbitrage/scripts/` — fx `check_nfts.py`, `check_pnl.py`, `check_today.py`, `check_db_state.py`, `db_report.py`. En **Trading Status Agent** kan (hvis du vil) køre disse og opsummere output i status-board eller chat.

---

## 5. Dashboard og status

- **Dashboard:** `dashboard/index.html` — links til logs og status.
- **Status-board:** Instant Mesh har `status-board.md`; du kan tilføje en **trading-status** sektion (manuelt eller via Trading Status Agent) så alt ligger ét sted.

---

## 6. Konkret: hvad du kan gøre nu

1. **Research / Profit Validator:** Når du overvejer ny collection eller strategi, kør Research Agent eller Profit Validator med en kort brief; brug output som input til beslutning (GO/NO-GO, krav til data).
2. **Trading Status Agent:** Brug prompten i `workspace/agents/TRADING_STATUS_AGENT.md` (manuelt session eller via cron). Den læser `workspace/projects/nft-arbitrage/TRADING_SYSTEM_VISION.md`, `notes/OBSERVATION_LOOP_OG_FORECAST_GATE.md` (i nft-arbitrage: `notes/`) og evt. scripts-output og laver en kort status.
3. **Status Weaver:** Udvid dens input-liste til at inkludere en fil som `workspace/projects/nft-arbitrage/status-board.md` eller `logs/trading-status.md` (hvis du får Trading Status Agent til at skrive der), så den samlede status-board viser både Instant Mesh og trading.
4. **Cron-job for trading status:** Tilføj et nyt job i `cron/jobs.json` (eller via `openclaw cron add` når gateway kører) med payload der trigger Trading Status Agent; kør fx dagligt kl. 09:00.

---

## 7. Kort oversigt

| OpenClaw-komponent | Brug til NFT arbitrage |
|--------------------|-------------------------|
| Cron + gateway | Kør Trading Status Agent (eller anden agent) på plan. |
| Research Agent | Valider nye collections/strategier før build. |
| Profit Validator | GO/NO-GO på nye ideer (strategier, chains). |
| Status Weaver | Inkluder trading-status i samlet status-board. |
| CORE-F | Fælles sprog for Comprehend/Evaluate/Fine-tune (observation, forecast, tuning). |
| Dashboard | Link til trading-logs / status når de findes. |
| Scripts (workspace + nft-arbitrage) | Agenter kan køre check_pnl, check_db_state osv. og opsummere. |

Alt det der allerede er gang i her (cron, agents, runbooks, dashboard) kan altså bruges til at **drive og overvåge** NFT-arbitrage uden at du behøver flytte koden — du tilkobler via agent-prompts, status-filer og evt. ét ekstra cron-job.
