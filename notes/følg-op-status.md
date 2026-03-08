# Følg-op: er alt som det skal være?

**Dato:** 2026-02-28

## Verificeret

| Tjek | Status |
|------|--------|
| **cron/jobs.json** | 3 jobs (instant-mesh-build, instant-mesh-investor, instant-mesh-status), valid JSON, korrekte schedule/message/delivery |
| **scripts/start-gateway.ps1** | Findes, sætter port 18789 + token, kalder node/gateway |
| **dashboard/index.html** | Findes, links til logs, status-board, CHECKLIST, runbook, cron-oversigt |
| **START-HER.md** | Findes, trin 1–3 (start gateway, cron list, evt. cron run) |
| **cron/README.md** | Findes, forklarer genstart + jobs.json |
| **Agent-prompts** | BUILD_CONDUCTOR.md, INVESTOR_SCOUT.md, STATUS_WEAVER.md under workspace/agents/instant-mesh/ |
| **Instant Mesh logs** | build-log.md, investor-log.md, dataset-log.md, status-board.md findes |
| **CHECKLIST.md** | Cron + dashboard markeret Done; wallet/reklame stadig Todo |

## Cron-job detaljer (som de skal være)

- **instant-mesh-build:** `0 8 * * *` Europe/Copenhagen, isolated, announce — prompt peger på BUILD_CONDUCTOR.md og logs/build-log.md.
- **instant-mesh-investor:** `0 10 * * 1,3` (man/ons 10:00), INVESTOR_SCOUT.md, investor/status.md + logs/investor-log.md.
- **instant-mesh-status:** `0 20 * * *` (dagligt 20:00), STATUS_WEAVER.md, status-board.md.

Stierne i messages bruger `workspace/...` — det matcher openclaw.json workspace (`C:\Users\Jnkri\.openclaw\workspace`).

## Ét skridt du stadig skal gøre

- **Genstart gatewayen** (hvis den kører), så den læser den nye `cron/jobs.json`. Efter genstart er de 3 jobs aktive på de angivne tidspunkter.

## Opsummering

Alt der er sat op i repo er som det skal være. Når gatewayen er startet (eller genstartet), er cron klar og dashboard/CHECKLIST/START-HER giver samme billede.
