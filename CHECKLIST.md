# OpenClaw — status & checkliste (fra Telegram + Cursor)

Opdateres løbende. **Done** = færdig; **In progress** = i gang; **Blocked** = venter; **Todo** = ikke startet.

---

## 1. Infrastruktur / miljø

| Task | Status | Note |
|------|--------|------|
| Pip-install split i batcher | **Done** | 4 batch-filer + `install-deps-batched.ps1` i OpenClaw-roden |
| Fælles .venv for hele OpenClaw | **Done** | `c:\Users\Jnkri\.openclaw\.venv` |
| RUNBOOK (Defender, cron, commit) | **Done** | `RUNBOOK.md` |
| PYTHON.md (ét miljø) | **Done** | Aktiver: `.venv\Scripts\Activate.ps1` fra roden |
| Deps 100% installeret i root-venv | **In progress / Tjek** | Kør `.\install-deps-batched.ps1` hvis usikker |

---

## 2. Cron & agents

| Task | Status | Note |
|------|--------|------|
| Cron-jobs registreret (gateway) | **Done** | `cron/jobs.json` har 3 jobs. **Genstart gateway** så den indlæser dem. Se `cron/README.md`. |
| Plan bring til live | **Done** | `notes/plan-bring-til-live.md` — gateway startet af agent 2026-03-06; resten: tjek Telegram + cron list. |
| BuildConductor prompt + run-script | **Done** | `workspace/scripts/run_build_conductor.ps1` + `agents/instant-mesh/BUILD_CONDUCTOR.md` |
| InvestorScout prompt + run-script | **Done** | `workspace/scripts/run_investor_scout.ps1` + tilsvarende agent-doc |
| Trading Status Agent (NFT arbitrage) | **Done** | `workspace/agents/TRADING_STATUS_AGENT.md` + `workspace/scripts/run_trading_status_agent.ps1`; kan tilføjes som cron-job (se notes/openclaw-og-nft-arbitrage.md) |
| Wallet-autopilot script + cron | **In progress** | Wallet-monitor (gas/spread polling, logformat, PnL) under udvikling i nft-arbitrage; cron når script er klar |
| Auto-summaries i chat | **Todo** | Afhænger af cron + delivery (announce) |

---

## 3. Agent-ramme (CORE-F + prompt-hacks)

| Task | Status | Note |
|------|--------|------|
| CORE-F i overordnet agent-dokumentation | **Done** | `notes/agent-system.md` i OpenClaw-roden — CORE-F + prompt-hacks |
| 25 Prompt-hacks som katalog | **Done** | Udvalgte hacks i `notes/agent-system.md`; udvid i `workspace/skills/prompts/` |
| Agent templates (CORE-F + hacks) | **Partial** | Per-projekt specs beskrevet i notes/agent-system.md; `agents/templates/` kan tilføjes senere |
| Instant Mesh agent-system.md | **Done** | Findes under instant-mesh/notes/; henviser nu til roden CORE-F |

---

## 4. Dashboard + checkliste

| Task | Status | Note |
|------|--------|------|
| CHECKLIST.md (denne fil) | **Done** | Opdateres ved milepæler |
| OpenClaw Control Center (dashboard) | **In progress** | Statisk `dashboard/index.html` (links) findes; Vite+Tailwind-app med kanban/metrics fra statusfiler under opbygning |
| Status-board pr. projekt | **Partial** | instant-mesh har logs/status; samlet view mangler |
| Kort autosummary i chat | **Todo** | Via cron når jobs kører |

---

## 5. Projekter

| Projekt | Status | Næste |
|---------|--------|--------|
| **Instant Mesh** | ✅ Datasæt-plan færdig (pacs.008 + syntetisk generator under datasets/). CORE-F + prompt-hacks i notes/agent-system.md. 🚧 Monorepo-skeleton (backend/agents/ui/infra) + README/justfile/devcontainer under opbygning. | BuildConductor næste step; ingen blokering. |
| **NFT Arbitrage / Wallet** | Backend-venv virker. ✅ Observation loop + forecast gate + decision knowledge (kun trade hvor vi forecast lige så godt som benchmark). 🚧 Wallet-monitor (gas/spread, PnL) under udvikling. | OpenClaw kan bruges: Research/Profit Validator til nye collections; Trading Status Agent + evt. cron (se notes/openclaw-og-nft-arbitrage.md). |
| **Dashboard** | ✅ CHECKLIST med CORE-F checkboxes. 🚧 Responsiv web (Vite + Tailwind) under opbygning; data-feed fra statusfiler; kanban + metrics. **Ops Control UI** (styre opgaver på tværs af ny/gammel PC, cloud, disk) er planlagt — se `notes/setup-ny-gammel-computer.md`. | Data-binding klar → kode uploades. |
| **Setup ny + gammel computer** | **Todo** | Én OpenClaw på tværs af begge maskiner: se `notes/setup-ny-gammel-computer.md` (Vej A: Tailscale/SSH; Vej B: synkroniseret workspace, én gateway ad gangen). |
| **OpenClaw på cloud (VPS)** | **Klar til opsætning** | Runbook med alle kommandoer: `notes/cloud-deployment-runbook.md`. Start her: `notes/START-HER-CLOUD.md`. Filer: `scripts/start-gateway.sh`, `scripts/openclaw-gateway.service`, `scripts/.env.cloud.example`. |
| **Reklamefilms-generator** | **Todo** | Nyt projekt: brief → storyboard/script/shotliste. |

---

## 6. Grønt lys (fra Telegram)

- **Cron/agents:** Du har givet grønt lys — lad gateway køre, hold Telegram-forsvaret nede så auto-summaries kan poste.
- **Commit:** Grønt lys til at committe til `main` eller `dev`; forslog branch-struktur (dev → main).
- **Pip:** Batched install + evt. Defender-whitelist af `C:\Users\Jnkri\.openclaw\workspace`.

---

*Sidst opdateret: 2026-03-08. Terminalarbejde køres af agenten selv (gateway-start, run_cycle, status) via `scripts/run-terminal-tasks.ps1` eller direkte kommandoer.*
