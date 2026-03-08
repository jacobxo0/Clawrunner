# Ollama + OpenClaw — hvad mangler og hvordan det kobles op

Sådan kører du **Ollama** (lokale modeller) med OpenClaw som I har talt om i chatten.

---

## Hvad der skal bygges/kobles op

| # | Ting | Status | Hvad du gør |
|---|------|--------|-------------|
| 1 | **Ollama installeret** | Todo | Download og installér fra [ollama.ai](https://ollama.ai). På Windows: kør installer, Ollama kører som service eller i baggrund. |
| 2 | **Ollama kører** | Todo | Tjek at `ollama serve` kører (eller at Windows-tjenesten er startet). Port **11434**. Test: `curl http://localhost:11434/api/tags` eller `ollama list`. |
| 3 | **Mindst ét tool-capable model** | Todo | OpenClaw bruger kun modeller der understøtter tools. Pull fx: `ollama pull llama3.3` eller `ollama pull qwen2.5-coder:32b` eller `ollama pull gpt-oss:20b`. Se `ollama list`. |
| 4 | **OpenClaw kender Ollama** | Gør vi nu | Sæt `OLLAMA_API_KEY` i det miljø hvor **gatewayen** kører (fx i `scripts/start-gateway.ps1`), eller brug `openclaw config set models.providers.ollama.apiKey "ollama-local"`. |
| 5 | **Vælg Ollama som model (valgfrit)** | Gør vi nu | I `openclaw.json`: sæt `agents.defaults.model.primary` til fx `ollama/llama3.3`, eller brug `fallbacks` så Ollama er backup til GPT/Claude. |
| 6 | **Genstart gateway** | Efter 4+5 | Ændringer i config kræver genstart af gatewayen. Stop den, start igen med `.\scripts\start-gateway.ps1`. |

---

## Vigtigt fra OpenClaw-docs

- **Brug ikke** `/v1` i URL til Ollama. OpenClaw bruger Ollamas **native API** (`http://host:11434` uden `/v1`) så tool calling virker. OpenAI-compatible `/v1` kan give fejl med tools.
- **Auto-discovery:** Hvis du *kun* sætter `OLLAMA_API_KEY` og *ikke* definerer `models.providers.ollama` i config, finder OpenClaw selv modellerne på `http://127.0.0.1:11434` (kun modeller der rapporterer tool support).
- **Context:** Ollama bruger ofte 2K–8K context som standard. For store agent-prompts kan det være nødvendigt at sætte `OLLAMA_NUM_CTX=16384` eller højere i miljøet hvor Ollama kører (ellers kan kontekst blive skåret).

---

## Konkret: ændringer i dit setup

### A) Miljøvariabel til gatewayen

I **`scripts/start-gateway.ps1`** (eller det sted du starter gatewayen), tilføj før `node`/`openclaw.mjs`:

```powershell
$env:OLLAMA_API_KEY = "ollama-local"
```

Så snart Ollama kører på samme maskine (eller på en host gatewayen kan nå), vil OpenClaw auto-discover modellerne.

### B) Valgfri: Ollama som primær eller fallback i openclaw.json

Under `agents.defaults`:

- **Kun Ollama:** `"model": { "primary": "ollama/llama3.3" }` (brug det model-id du har pull’et).
- **Ollama som backup:** Behold `primary` som GPT/Claude og tilføj fx `"fallbacks": ["ollama/llama3.3"]`.
- **Alias:** Under `agents.defaults.models` kan du tilføje `"ollama/llama3.3": { "alias": "Ollama" }` så du nemt kan skifte.

Efter ændring: genstart gateway.

---

## Tjek at det virker

1. `ollama list` — du skal se mindst én model.
2. `ollama serve` kører (eller tjenesten er startet).
3. Start gateway med `OLLAMA_API_KEY` sat.
4. `openclaw models list` (mens gateway kører) — Ollama-modeller skal optræde.
5. Skift primary til `ollama/<model-id>` og send en besked via Telegram eller WebChat; agenten skal bruge Ollama.

---

## Hvis Ollama kører på en anden maskine

Hvis Ollama står på fx gammel PC og gatewayen på ny PC: brug **explicit provider** i `openclaw.json` med `baseUrl: "http://<ip-af-gammel-pc>:11434"` (uden `/v1`), og definér `models.providers.ollama` med `api: "ollama"` og de modeller du vil bruge (auto-discovery slås fra når du sætter explicit provider).

---

*Sidst opdateret: 2026-03-06. Baseret på docs.openclaw.ai/providers/ollama og gateway/local-models.*
