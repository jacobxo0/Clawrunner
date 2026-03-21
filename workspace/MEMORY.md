# MEMORY.md — Long-term curated memory

Kun læses i main session (direkte chat med Jacob). Opdateres med beslutninger, læring og kontekst der ikke må gå tabt. Daglige noter ligger i `memory/YYYY-MM-DD.md`.

---

## Beslutninger

- **Clawrunner på Railway:** Gateway kører på `https://clawrunner-production.up.railway.app`; Telegram, cron og OpenClaw CLI peger her. UI (Clawrunner Control Center) er frontend til denne instans.
- **Eget AI-ops system:** Bygge et helt eget system med fokus på sikkerhed, kontrol, modulær runtime og eget UI (ikke afhængigt af Claw).
- **Custom Claw projekt:** Cloud-core, desktop, light/mobile med shared-state, multi-agent koordination og UI/Telegram kontrol.
- **Instant Mesh Phase 1:** Venter på approvals (Phase 0→1, PDF-spejling, raise/dilution, PSP-introer) — status i build-log.md.

---

## Læring

- **CORE-F:** Comprehend → Orchestrate → Respond → Evaluate → Fine-tune; alle agenter følger denne cyklus. Se `notes/agent-system.md`.
- **Historik og learning bevares:** memory/ + MEMORY.md; Clawrunner UI viser links og evt. summaries. Ingen arkiv eller sletning af eksisterende arbejde.
- **Execution discipline:** Agent kører terminalarbejde selv (gateway, cron, run_cycle); deploy når der leveres; følg build-logs efter deploy. Se workspace/AGENTS.md.
- **Selvforbedring:** Systemet er sat op til at træne sig selv fra samtalehistorik og memory — læs `workspace/notes/self-improvement.md`; forslag gemmes i `workspace/IMPROVEMENTS-BACKLOG.md`; agenten gennemgår memory + (i Cursor) agent-transcripts og tilføjer forbedringer, implementerer små og opdaterer MEMORY.md.
- **Capability-loops:** Orchestratoren opretter work units der **tilføjer kompetencer** (regler/skills) når: kun snak uden eksekvering, for lidt output, eller gentagne fejl. Læs `workspace/notes/capability-loops.md`. Escalation fra swarm-kernel bliver til work unit "Add competency" → Execute → QC → Release. Cron: capability-loop (søndag 21:00); swarm-cycle inkluderer capability-tjek efter hver cyklus.

---

## Blokkeringer / ACTION REQUIRED

- Instant Mesh: Phase 1-approvals, ECB/EPC PDF-spejling, raise target, design-partner PSP shortlist (se build-log.md).
- Wallet-autopilot: Under udvikling; cron-job når script er klar.

---

## Referencer

- CHECKLIST.md, RUNBOOK.md, START-HER.md, notes/ — single source of truth for status og runbooks.
- workspace/intake/ — seneste opgaver fra Telegram.
- workspace/memory/YYYY-MM-DD.md — daglige raw logs.

*Oprettet 2026-03-08. Opdater med beslutninger og læring efter behov.*
