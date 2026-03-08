# Plan: Bring OpenClaw til live

Eksekveringsplan for at få systemet kørende. Udføres i rækkefølge.

---

## Fase 1 — Gateway + Telegram (nu)

| # | Handling | Ansvar | Status |
|---|----------|--------|--------|
| 1.1 | Start gatewayen | Du eller agent | [x] 2026-03-06 (agent startede gateway) |
| 1.2 | Verificer port 18789 lytter: `netstat -an \| findstr 18789` | Du eller agent | [x] Port 18789 LISTENING |
| 1.3 | Tjek Telegram: send en besked til botten (DM eller @mention i gruppe) | Du | [ ] |
| 1.4 | Verificer intake: tjek `workspace/intake/telegram/YYYY-MM-DD.md` for ny post | Agent ved næste turn | [ ] |

**Kommando til 1.1:**  
`cd c:\Users\Jnkri\.openclaw; .\scripts\start-gateway.ps1`  
(Lad vinduet køre eller start i baggrund.)

---

## Fase 2 — Cron (allerede konfigureret)

| # | Handling | Status |
|---|----------|--------|
| 2.1 | Gateway læser `cron/jobs.json` ved start — 3 jobs (instant-mesh-build 08:00, investor man/ons 10:00, status 20:00) | ✅ Konfigureret |
| 2.2 | Efter gateway start: `openclaw cron list` — bekræft at jobs vises | [x] 2026-03-06: 3 jobs vist (instant-mesh-build, instant-mesh-status, instant-mesh-investor), alle ok |
| 2.3 | (Valgfrit) Kør ét job nu: `openclaw cron run <uuid>` — tjek build-log.md for ny post | [x] Forsøgt; CLI fik gateway timeout 30s. build-log seneste post: 2026-03-06 13:45 CET. Kør evt. manuelt med længere ventetid. |

---

## Fase 3 — Ollama (valgfrit, lokale modeller)

| # | Handling | Status |
|---|----------|--------|
| 3.1 | Installér Ollama fra ollama.ai | [ ] |
| 3.2 | Pull model: `ollama pull llama3.3` (eller qwen2.5-coder / gpt-oss:20b) | [ ] |
| 3.3 | Ollama kører på 11434 (`ollama serve` eller Windows-tjeneste) | [ ] |
| 3.4 | Genstart gateway (den har allerede OLLAMA_API_KEY i start-script) | [ ] |
| 3.5 | `openclaw models list` — Ollama-modeller skal optræde | [ ] |
| 3.6 | (Valgfrit) Sæt primary/fallback i openclaw.json til ollama/<model> | [ ] |

Se **notes/ollama-setup.md** for detaljer.

---

## Fase 4 — Dashboard + opsyn

| # | Handling | Status |
|---|----------|--------|
| 4.1 | Åbn dashboard: `dashboard/index.html` (eller `python -m http.server` i dashboard-mappen) | [ ] |
| 4.2 | Bookmark CHECKLIST.md, RUNBOOK.md, START-HER.md til hurtig adgang | [ ] |

---

## Efter udførelse

- **Live betyder:** Gateway kører → Telegram svarer, cron kører på plan, intake fanger beskeder.
- **Du skal selv:** Starte (eller lade agenten starte) gatewayen og evt. bekræfte Telegram + cron list.
- **Ollama:** Kun nødvendig hvis du vil bruge lokale modeller; ellers er GPT/Claude nok.

---

*Plan oprettet: 2026-03-06. Opdater status efterhånden som trin udføres.*
