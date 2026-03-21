# Integrationer – oversigt og hvad der mangler

## Aktive integrationer

### Kanaler (channels)
| Kanal    | Status   | Config / noter |
|----------|----------|----------------|
| Telegram | Aktiv    | `openclaw.json` → `channels.telegram` (botToken, dmPolicy, groupPolicy). Plugin: `plugins.entries.telegram` |
| Slack    | Klar, slået fra | Config tilføjet. **Aktiver:** sæt env `SLACK_APP_TOKEN` (xapp-…) og `SLACK_BOT_TOKEN` (xoxb-…), sæt `channels.slack.enabled` til `true`. |
| Discord  | Klar, slået fra | Config tilføjet. **Aktiver:** tilføj `channels.discord.botToken` (fra Discord Developer Portal), sæt `channels.discord.enabled` til `true`. |

### Skills (ClawHub / workspace)
| Skill                      | Kilde        | Noter |
|----------------------------|--------------|--------|
| openclaw-github-assistant  | ClawHub      | Config i `skills.entries.github` (GITHUB_TOKEN, GITHUB_USERNAME). |
| investor                   | ClawHub      | I `workspace/skills/investor`. |
| afrexai-startup-fundraising| ClawHub      | I `workspace/skills/afrexai-startup-fundraising`. |
| notion-api-integration     | ClawHub      | **Ny** – i `workspace/skills/notion-api-integration`. Kræver `NOTION_API_KEY` (env eller config). Første gang: læs `workspace/skills/notion-api-integration/setup.md`. |

### Cron
- Jobs registreret i gateway; IDs er **UUID** (ikke navn). Se `cron/jobs.json` og `cron/CRON-SETUP.md`.
- Kør: `openclaw cron run <uuid>` når gateway kører (fx `scripts/start-gateway.ps1`).

---

## Hvad der er hentet / tilføjet

- **notion-api-integration** – installeret med `clawhub install notion-api-integration` (fra workspace). Tilgængelig som skill; sæt `NOTION_API_KEY` for at bruge Notion API.

---

## Sådan tilføjer du flere integrationer

1. **Flere skills fra ClawHub**  
   Fra workspace:  
   `npx clawhub search <søgeord> --limit 10`  
   `npx clawhub install <slug> --no-input`  
   Evt. env/config i `openclaw.json` under `skills.entries.<slug>` hvis skill’en kræver det.

2. **Slack som kanal**  
   Config findes allerede. Opret Slack-app (Socket Mode), hent app token + bot token. Sæt env `SLACK_APP_TOKEN` og `SLACK_BOT_TOKEN`, og sæt `channels.slack.enabled` til `true` i `openclaw.json`.

3. **Discord som kanal**  
   Config findes allerede. Opret app i [Discord Developer Portal](https://discord.com/developers/applications), hent Bot Token, tilføj bot til server. I `openclaw.json`: tilføj `"botToken": "dit-token"` under `channels.discord` og sæt `"enabled": true`.

4. **Cron**  
   Nye jobs: `openclaw cron add …` (når gateway kører). Brug altid det returnerede UUID til `cron run`.

---

## Referencer

- Cron: `cron/README.md`, `cron/CRON-SETUP.md`
- Gateway: `scripts/start-gateway.ps1`, `RUNBOOK.md`
- OpenClaw channels: https://docs.openclaw.ai/channels/
- ClawHub: søg/install fra `workspace`-mappen
