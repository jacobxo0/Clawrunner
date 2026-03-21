# Clawrunner agent-arkitektur — overordnet oversigt

Ét samlet billede af roller, dataflow og UI. Detaljer står i de linkede filer; ingen duplikation af historik.

---

## 1. CORE-F og prompt-hacks

Alle agenter følger **CORE-F**: Comprehend → Orchestrate → Respond → Evaluate → Fine-tune. Prompt-hacks (Role assignment, Two-pass, Checklist, osv.) og per-projekt specs:

- **[notes/agent-system.md](agent-system.md)** — CORE-F, prompt-katalog, feedback/learning (F).

---

## 2. Roller

| Rolle | Beskrivelse | Hvor |
|-------|-------------|------|
| **Gateway (Clawrunner)** | OpenClaw gateway; Telegram, cron, sessions, CLI. | Railway: `https://clawrunner-production.up.railway.app` |
| **Cron** | Scheduler for BuildConductor, InvestorScout, StatusWeaver (evt. Trading Status). | `cron/jobs.json`; gateway læser ved start. |
| **BuildConductor** | Phase 0–3 tekniske opgaver (Instant Mesh). | Cron 08:00 CET; prompt i `workspace/agents/instant-mesh/BUILD_CONDUCTOR.md` |
| **InvestorScout** | Target list, deck/memo, outreach (ingen sends). | Cron man/ons 10:00 CET. |
| **StatusWeaver** | Samler build-log + investor/status; poster kort summary + status-board. | Cron 20:00 CET. |
| **Trading Status Agent** | NFT arbitrage status. | Run-script findes; kan tilføjes som cron-job. |
| **Ops Control UI** | Central styring på tværs af PC/cloud/disk. | Clawrunner UI (dashboard + evt. Vite-app). |
| **Telegram** | Intake og svar; samme gateway som cron. | Bot token i Railway Variables. |
| **CLI** | `openclaw --gateway https://clawrunner-production.up.railway.app <command>`. | Fra Jacob's PC med OPENCLAW_GATEWAY_TOKEN. |

---

## 3. Dataflow

```
intake (Telegram/CLI)
    → memory/ + MEMORY.md + CHECKLIST
    → agent-prompts (BuildConductor, InvestorScout, …)
    → cron/sessions (gateway)
    → logs/status (build-log.md, investor/status.md, status-board.md)
    → StatusWeaver/summary
    → chat + status-board
```

Clawrunner UI er **single pane of glass**: links til logs, status-board, gateway (health), cron-liste, memory/intake (evt. summaries). **Token aldrig i frontend.** For at vise live cron list eller gateway health i UI skal du bruge en **backend-proxy**: et server-side endpoint der kalder gateway med `OPENCLAW_GATEWAY_TOKEN` fra miljøvariabel og returnerer kun læsbare data til frontend. Se `dashboard-app/README.md` (Gateway-proxy).

---

## 4. Ops Control UI (udvidelse af dashboard)

- **Spec:** [notes/setup-ny-gammel-computer.md](setup-ny-gammel-computer.md) — central UI på tværs af gammel PC, ny PC, cloud, disk.
- **Backend:** Kan kalde gateway API (health, cron list) så UI styrer samme gateway som Telegram/cron. Token kun på server/proxy.
- **Frontend:** Dashboard (statisk) og/eller Vite+Tailwind-app med kanban/metrics fra statusfiler; branding = Clawrunner (logo i header).

---

## 5. Referencer

- CORE-F + hacks: [notes/agent-system.md](agent-system.md)
- Instant Mesh agenter: [workspace/projects/instant-mesh/notes/agent-system.md](../workspace/projects/instant-mesh/notes/agent-system.md)
- Ops Control: [notes/setup-ny-gammel-computer.md](setup-ny-gammel-computer.md)
- Cron: [cron/CRON-SETUP.md](../cron/CRON-SETUP.md)
- Checklist: [CHECKLIST.md](../CHECKLIST.md), Runbook: [RUNBOOK.md](../RUNBOOK.md)

*Oprettet 2026-03-08. Opdater ved ændringer i roller eller dataflow.*
