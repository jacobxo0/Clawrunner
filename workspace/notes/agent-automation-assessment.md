# Overordnet vurdering: Agent-automation i samtalen

**Formål:** Vurdere hvor agent-systemet kunne have gjort mere automatisk i denne samtale, og implementere det som forbedringer.

---

## 1. Hvad der skete i samtalen (kort)

- Swarm/loop-setup, capability-loops, fix-loop uden at spørge om lov
- Telegram-test + push, "fetch failed" → Ollama/config, docs (RUNBOOK, fetch-failed, ollama-setup)
- Ollama på server (Hetzner), config skift mellem 127.0.0.1 og 46.225.168.46
- Test-loop med server-først og lokal fallback; BOM i openclaw.json fikset manuelt
- Telegram "API fejl" → forbedret fejlvisning (rigtig API-besked)

---

## 2. Hvor der kunne have været mere automatisk

### 2.1 Config / BOM

- **Observation:** validate-ollama fejlede med "Unexpected token '﻿'" (UTF-8 BOM). Løsningen blev at køre et one-off script for at fjerne BOM.
- **Mere automatisk:** Agent-systemet burde **ved første JSON-parse-fejl på openclaw.json** automatisk strippe BOM og fortsætte (eller prøve igen). Det kræver ikke brugerens input.
- **Implementering:** I validate-ollama (og evt. andre scripts der læser config): læs rå bytes/string, strip BOM hvis `\uFEFF`, parse derefter. Alternativt: et fælles "ensure-config" trin før scripts der bruger openclaw.json.

### 2.2 Ollama connection (ECONNREFUSED / timeout)

- **Observation:** Config pegede på server (46.225.168.46); fra Cursor-miljøet var serveren utilgængelig (ECONNREFUSED). Løsningen var test-loop med `-FallbackLocal` og manuel/viden om "kør fra din PC mod server".
- **Mere automatisk:** **Ved forbindelsesfejl til konfigureret baseUrl** burde systemet automatisk prøve 127.0.0.1:11434 og rapportere begge udfald ("server nås ikke; lokal OK" eller "begge fejler"). Så behøver brugeren ikke vide at der findes en fallback – det sker i én kørsel.
- **Implementering:** validate-ollama med flag (fx `--try-local`) eller miljøvariabel: ved ECONNREFUSED/timeout prøv lokal URL og skriv klar status.

### 2.3 Telegram API-fejl

- **Observation:** Brugeren fik "api fejl på telegram besked" uden at se den konkrete fejl. Vi tilføjede udskrivning af Telegram API response body (description).
- **Mere automatisk:** Ved "chat not found" kunne agenten **automatisk foreslå eller køre getUpdates** og udskrive "Mulige chat_id: ...". Ved "Unauthorized" kunne en one-liner i RUNBOOK eller i scriptet fortælle præcis hvad der skal tjekkes. Så reduceres "hvad betyder det?" til et enkelt kørsel/kommando.
- **Implementering:** Telegram-fejl vises nu; kan udvides med et lille diagnose-script (getMe + getUpdates) der udskriver anbefalede chat_id'er.

### 2.4 Gateway start og "klar"

- **Observation:** Test-loop starter gateway og venter 6 sekunder; model-kald gav timeout – gateway var måske ikke klar endnu.
- **Mere automatisk:** **Vente på at gateway reelt svarer** (poll /health eller port åben) med backoff og max ventetid, i stedet for fast sleep. Samme mønster i ensure-ollama-gateway-loop og test-loop.
- **Implementering:** Fælles Wait-GatewayReady (poll TCP eller HTTP) med timeout; brug i test-loop og evt. ensure-ollama-gateway-loop.

### 2.5 Én indgang: preflight / doctor

- **Observation:** Der er mange scripts: test-loop, ensure-ollama-gateway-loop, debug-push-telegram, force-ollama-server, telegram-test-loop. Brugeren og agenten skal vide hvilken der skal køres hvornår.
- **Mere automatisk:** **Ét preflight/doctor-script** der: (1) sikrer openclaw.json er valid (strip BOM), (2) kører validate ollama (evt. med try-local), (3) tjekker gateway-port, (4) evt. Telegram getMe. Én kørsel giver fuld status og retter det der kan rettes automatisk (fx BOM).
- **Implementering:** scripts/preflight-openclaw.ps1 (eller npm run preflight) der kalder de nødvendige tjek og retter config hvis muligt.

### 2.6 Swarm / capability-regler

- **Observation:** Gentagne mønstre (BOM, ECONNREFUSED, Telegram fejl) blev løst ad hoc i dialogen. Capability-escalation i swarm-kernel siger at ved gentagne fejl skal der tilføjes kompetence (skill/regel).
- **Mere automatisk:** **Eksplicitte regler til agenten:** "Ved JSON-parse-fejl på openclaw.json: strip BOM og prøv igen"; "Ved validate-ollama connection failure: prøv lokal fallback og rapporter begge"; "Ved Telegram sendMessage-fejl: udskriv API description og evt. kør getMe/getUpdates." Så vælger agenten automatisk den rigtige handling uden at brugeren behøver beskrive fejlen.
- **Implementering:** Sektion i AGENTS.md og i swarm-kernel reference: "Automatic responses" med de konkrete trigger → handling.

---

## 3. Implementerede forbedringer (dette arbejde)

| Forbedring | Hvor |
|------------|------|
| BOM-tolerance ved config-læsning | validate-ollama.js (strip BOM før parse) |
| Valgfri lokal fallback ved connection failure | validate-ollama.js (--try-local) |
| Preflight: config + Ollama + gateway + Telegram getMe | scripts/preflight-openclaw.ps1, npm run preflight |
| Wait-GatewayReady med polling | test-loop.ps1 (evt. ensure-ollama-gateway-loop) |
| Automatiske agent-responser (BOM, Ollama, Telegram) | AGENTS.md + swarm-kernel reference.md |

---

## 4. Kort opsummering

**Agent-systemet kunne have været mere automatisk ved:**

1. At rette config-problemer (BOM) uden at brugeren skulle nævne det.
2. At prøve lokal Ollama ved server-connection-fejl og rapportere begge udfald i én kørsel.
3. At vise og evt. diagnosticere Telegram API-fejl (getMe/getUpdates) automatisk.
4. At vente på at gateway er klar (poll) i stedet for fast sleep.
5. At have ét preflight-script der samler tjek og auto-fixes (fx BOM).
6. At have skrevne regler så agenten ved "ved denne fejltype → gør dette" uden ekstra bruger-input.

Disse er nu implementeret eller dokumenteret, så fremtidige sessioner og swarm-cykler kan gøre mere automatisk fra agent-siden.
