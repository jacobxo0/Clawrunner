# Clawrunner (OpenClaw Gateway Deploy)

Deployment configuration and scripts for an OpenClaw AI gateway (Telegram bot backed by Groq LLM). See `CLAUDE.md` for debug history and `CHECKLIST.md` for project status.

## Cursor Cloud specific instructions

### Project structure

This is a **deployment-configuration project**, not a traditional application. It wraps the `openclaw` npm package (single dependency) with config templates, startup scripts, and agent/skill definitions. There is no custom source code, no linter, no test suite, and no build step.

### Running the gateway locally

1. Install dependencies: `npm install`
2. Build config from template: `node scripts/build-config.js /workspace` (requires env vars below)
3. Copy config: `mkdir -p ~/.openclaw/agents/main/sessions ~/.openclaw/credentials && cp openclaw.json ~/.openclaw/openclaw.json && chmod 700 ~/.openclaw && chmod 600 ~/.openclaw/openclaw.json`
4. Start gateway: `npx openclaw gateway run --port 18789 --dev --allow-unconfigured --verbose`

### Required environment variables

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Groq LLM API key (primary model provider) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather |
| `OPENCLAW_GATEWAY_TOKEN` | Gateway auth token (any strong string) |

Optional: `BRAVE_API_KEY`, `OLLAMA_API_KEY`, `OLLAMA_BASE_URL`, `TELEGRAM_GROUP_ALLOW_FROM` (JSON array of allowed Telegram user IDs).

### Config validation gotcha

The Telegram `dmPolicy: "allowlist"` requires `allowFrom` to contain at least one sender ID. When building config with `build-config.js`, set `TELEGRAM_GROUP_ALLOW_FROM` to a JSON array with at least one ID (e.g. `'["12345"]'`), otherwise `openclaw gateway run` will refuse to start with a config validation error.

### Ollama config gotcha

The Ollama provider in `openclaw.railway.example.json` uses `${OLLAMA_BASE_URL}`. If this env var is unset, it resolves to an empty string and OpenClaw rejects the config (`models.providers.ollama.baseUrl: Too small`). Always set `OLLAMA_BASE_URL` to a placeholder (e.g. `http://localhost:11434`) even if Ollama isn't available.

### Connecting to the Control UI

The gateway serves a web dashboard at `http://127.0.0.1:18789/`. To authenticate, use the tokenized URL from `npx openclaw dashboard --no-open` (outputs a URL with `#token=...`). Alternatively, paste the `OPENCLAW_GATEWAY_TOKEN` value into the Gateway Token field manually.

### Telegram 409 conflict

If another bot instance is running elsewhere (e.g. on Railway) with the same `TELEGRAM_BOT_TOKEN`, you'll see `getUpdates conflict (409)` errors. The gateway retries automatically; this does not prevent the gateway from functioning otherwise.

### Useful commands

- `npx openclaw --version` — check installed version
- `npx openclaw doctor` — run config/state diagnostics
- `npx openclaw dashboard --no-open` — get tokenized dashboard URL
- `npx openclaw gateway stop` — stop a running gateway
- `curl http://127.0.0.1:18789/healthz` — health check (gateway must be running)
- `node scripts/build-config.js /workspace` — rebuild config from template + env vars

### No lint/test/build

This project has no ESLint, TypeScript, test framework, or build pipeline. Quality checks are limited to verifying the gateway starts and responds on its HTTP/WS endpoints.
