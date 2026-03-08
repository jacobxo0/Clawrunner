# Brave Search API — live web research i OpenClaw

For at Research Agent (eller andre agenter) kan lave **live web research** (søgning, friske kilder til regulering, spreads, logistik) skal Brave Search API være konfigureret.

## 1. Nøgle

- Opret konto og hent API-nøgle: [brave.com/search/api/](https://brave.com/search/api/)
- Vælg **Data for Search** (ikke "Data for AI" — det er ikke kompatibelt med `web_search`).
- Gratis tier: 2.000 forespørgsler/måned.

## 2. Konfiguration i OpenClaw

**Option A — Interaktivt (anbefalet)**  
```bash
openclaw configure --section web
```
Indtast API-nøglen når du bliver bedt om det. Config opdateres automatisk.

**Option B — Manuelt i openclaw.json**  
I `openclaw.json` findes nu en `tools.web.search`-sektion. Sæt din nøgle i `apiKey`:
```json
"tools": {
  "web": {
    "search": {
      "provider": "brave",
      "apiKey": "DIN_BRAVE_API_NØGLE",
      "maxResults": 10,
      "timeoutSeconds": 30
    }
  }
}
```

**Option C — Miljøvariabel**  
Sæt `BRAVE_API_KEY` i det miljø hvor **gatewayen** kører. I dette setup er den sat i:
- `scripts/start-gateway.ps1` (når du starter med PowerShell)
- `gateway.cmd` (når du starter med gateway.cmd)

Hvis OpenClaw stadig siger "Brave ikke sat op", er det ofte fordi **gatewayen kører uden at have nøglen i miljøet** (fx startet før nøglen blev tilføjet). Løsning: stop gateway og start igen med `gateway.cmd` eller `.\scripts\start-gateway.ps1`.

## 3. Efter konfiguration

- Genstart gateway (så den læser ny config / env).
- Derefter kan agenter med adgang til `web_search` trække friske kilder; Research Agent kan udfylde rapporten med live-data (spreads, leverandører, regulering).

## 4. Reference

- [OpenClaw Brave Search (docs.openclaw.ai)](https://docs.openclaw.ai/brave-search)
- [CLI configure](https://docs.openclaw.ai/cli/configure)
