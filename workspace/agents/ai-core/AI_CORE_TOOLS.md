# AI-CORE Tool Execution

AI-CORE er en lokal-first orchestration platform der kører på Railway.
Du kan kalde AI-CORE tools direkte via HTTP fra dine agent-turns.

## Endpoint

```
POST ${AI_CORE_URL}/command
Content-Type: application/json

{
  "command": "<tool_name>",
  "arguments": { ... },
  "request_id": "<valgfrit>"
}
```

**Base URL:** Læs `${AI_CORE_URL}` fra environment (Railway Variable: `AI_CORE_URL`).
Standard lokalt: `http://localhost:8000`

## Tilgængelige tools

| Tool | Beskrivelse | Argumenter |
|------|-------------|------------|
| `healthcheck` | System health status | ingen |
| `system_info` | CPU, RAM, disk, platform | ingen |
| `echo` | Ekko en besked (test) | `message: string` |
| `run_check` | Kør shell-kommando | `command: string`, `timeout?: int` |
| `fetch_url` | HTTP GET en URL | `url: string`, `timeout?: int` |
| `query_runs` | Hent seneste tool-runs fra memory | `failed_only?: bool`, `limit?: int`, `tool_name?: string` |
| `suggest_fix` | Foreslå fix til fejl via Ollama | `error: string`, `tool_name?: string` |

## Svar-format (ToolResult)

```json
{
  "success": true,
  "output": { ... },
  "error": null,
  "tool_name": "healthcheck",
  "duration_seconds": 0.001,
  "request_id": null
}
```

## Eksempel — healthcheck

```http
POST http://localhost:8000/command
{"command": "healthcheck", "arguments": {}}
```

Svar:
```json
{"success": true, "output": {"status": "ok", "components": ["orchestrator", "tool_runner"]}, ...}
```

## Eksempel — system_info

```http
POST http://localhost:8000/command
{"command": "system_info", "arguments": {}}
```

## Eksempel — kør en kommando

```http
POST http://localhost:8000/command
{"command": "run_check", "arguments": {"command": "git status", "timeout": 10}}
```

## Dashboard og run-historik

- Dashboard: `${AI_CORE_URL}/ui`
- Run-historik JSON: `${AI_CORE_URL}/runs?failed=true&limit=20`
- Tool-liste: `${AI_CORE_URL}/tools`

## Fejlhåndtering

Hvis `success: false`: tjek `error`-feltet. Common årsager:
- Unknown tool: `"Unknown tool: 'xyz'"` — tjek tool-navnliste ovenfor
- Timeout: tool tog for lang tid — øg timeout eller undersøg tool
- AI-CORE nede: `fetch_url` returnerer connection error — tjek Railway Variables → AI_CORE_URL
