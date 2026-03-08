# Hvad OpenClaw rent faktisk gør lige nu

Kort og ærligt: hvad der **kører** vs. hvad der **er planlagt men ikke live**.

---

## Det der faktisk virker

| Ting | Status |
|------|--------|
| **Telegram-chat** | Gateway + bot er sat op. Når du skriver i Telegram (med @mention i grupper), svarer agenten (GPT/Claude) med adgang til workspace og skills. |
| **Telegram-intake** | Hver brugerbesked fanges i `workspace/intake/telegram/YYYY-MM-DD.md` med raw tekst + **HVAD SKAL SKE** (påbud i AGENTS.md). |
| **GitHub-skill** | Aktiveret med token – agenten kan lave issues, søge repos osv. når du beder om det. |
| **Manuelle agent-kørsel** | Du kan køre fx `workspace\scripts\run_build_conductor.ps1` – så spawner en isoleret agent-turn med BuildConductor-prompten. Det sker kun når **du** kører scriptet. |
| **Python-miljø** | nft-arbitrage har .venv med alle deps. OpenClaw-roden har også fælles .venv + batched install. |
| **NFT Arbitrage-app** | FastAPI-app i `projects/nft-arbitrage/src/main.py` – kan køres med `uvicorn` hvis du vil bruge den. |

---

## Det der er sat op (kræver genstart af gateway)

| Ting | Status |
|------|--------|
| **Cron** | `cron/jobs.json` har **3 jobs** (instant-mesh-build 08:00, instant-mesh-investor man/ons 10:00, instant-mesh-status 20:00). **Genstart gateway** så den indlæser dem – derefter kører de på plan. |
| **Dashboard** | `dashboard/index.html` – links til logs, status-board, checklist. |
| **Gateway-start** | `scripts/start-gateway.ps1` – kør fra OpenClaw-roden eller med `-OpenClawRoot`. |

## Det der stadig ikke kører

| Ting | Status |
|------|--------|
| **Wallet-autopilot** | Ikke bygget. |
| **Reklamefilms-generator** | Ikke startet. |
| **Auto-summaries i chat** | Kommer når cron kører (efter gateway-genstart). |

---

## Hvorfor det føles begrænset

OpenClaw som **platform** kan meget (chat, gateway, cron-motor, spawn, skills). Men hos dig er det meste **ubrugt** lige nu:

- Cron-motoren er der, og **3 jobs** er i `cron/jobs.json` (instant-mesh-build, -investor, -status); de kører når gatewayen kører.
- Agent-prompts og run-scripts findes, men de kører kun ved **manuelle** kald.
- Der er mange planer (wallet, reklame, dashboard), men **ingen af dem er leveret endnu**.

Så det der “gr” (gør) er i praksis: **svar i Telegram + manuel kørsel af et enkelt script**. Resten er forberedelse og dokumentation.

---

## Næste skridt (for at det hele kører)

1. **Genstart gatewayen**  
   Stop den nuværende gateway-proces (hvis den kører). Start igen med:
   ```powershell
   cd c:\Users\Jnkri\.openclaw
   .\scripts\start-gateway.ps1
   ```
   Så indlæses de 3 cron-jobs fra `cron/jobs.json`, og BuildConductor/InvestorScout/StatusWeaver kører på deres tider.

2. **Tjek at cron er loadet**  
   Mens gatewayen kører: `openclaw cron list` – du bør se instant-mesh-build, instant-mesh-investor, instant-mesh-status.

3. **Kør én job nu (valgfrit)**  
   `openclaw cron run instant-mesh-build` – så kører BuildConductor med det samme og skriver i build-log.md.

---

*Opdateret 2026-03-08. Cursor har forsøgt at starte gateway i baggrunden; for vedvarende kørsel: kør `.\scripts\start-gateway.ps1` i et dedikeret terminal og lad det stå åbent.*
