# OpenClaw cron — opsætning af jobs

Gatewayen håndterer `cron/jobs.json` selv. **Tilføj jobs via CLI** (når gateway kører) eller via Gateway cron-tool. Manual redigering af `jobs.json` er kun sikkert når gatewayen er stoppet.

---

## Kommandoer (kør fra PowerShell/CMD)

Udfør disse én ad gangen. `--announce` sender resultat til chat (Telegram/sidste kanal). Ændr `--to` hvis du vil have et bestemt chat/topic.

### 1. Instant Mesh — BuildConductor (dagligt 08:00 CET)

```bash
openclaw cron add --name "instant-mesh-build" --cron "0 8 * * *" --tz "Europe/Copenhagen" --session isolated --message "You are BuildConductor. Read and execute the instructions in workspace/agents/instant-mesh/BUILD_CONDUCTOR.md. Work in workspace/projects/instant-mesh. Log to logs/build-log.md. Report summary and any ACTION REQUIRED." --announce
```

### 2. Instant Mesh — InvestorScout (man + ons 10:00 CET)

```bash
openclaw cron add --name "instant-mesh-investor" --cron "0 10 * * 1,3" --tz "Europe/Copenhagen" --session isolated --message "You are InvestorScout. Read and execute workspace/agents/instant-mesh/INVESTOR_SCOUT.md. Work in workspace/projects/instant-mesh. Update investor/status.md and logs/investor-log.md. Report summary and any ACTION REQUIRED." --announce
```

### 3. Instant Mesh — StatusWeaver (dagligt 20:00 CET)

```bash
openclaw cron add --name "instant-mesh-status" --cron "0 20 * * *" --tz "Europe/Copenhagen" --session isolated --message "You are StatusWeaver. Read workspace/agents/instant-mesh/STATUS_WEAVER.md. Summarize build-log.md and investor/status.md (and wallet if present). Post short status to chat and update status-board.md." --announce
```

### 4. Wallet-autopilot (når script er klar — fx hver time)

```bash
openclaw cron add --name "wallet-autopilot" --cron "0 * * * *" --tz "Europe/Copenhagen" --session isolated --message "Run wallet monitor/autopilot per workspace docs. Dry-run only unless LIVE_TRADING=1. Log to projects/nft-arbitrage/logs/wallet-log.md. Post PnL summary if changed." --announce
```

*(Kør kun efter wallet_monitor / autopilot-script er implementeret og testet.)*

---

## Liste og kør manuelt

```bash
openclaw cron list
openclaw cron run <jobId>        # kør nu (force)
openclaw cron runs --id <jobId> # vis historik
openclaw cron edit <jobId> --message "Ny prompt"
openclaw cron remove <jobId>
```

---

## JSON-eksempel (til tool-call / reference)

Hvis du tilføjer jobs via Gateway API eller tool-call i stedet for CLI, brug denne form:

**Eksempel: instant-mesh-build (recurring isolated)**

```json
{
  "name": "instant-mesh-build",
  "schedule": { "kind": "cron", "expr": "0 8 * * *", "tz": "Europe/Copenhagen" },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "You are BuildConductor. Read and execute the instructions in workspace/agents/instant-mesh/BUILD_CONDUCTOR.md. Work in workspace/projects/instant-mesh. Log to logs/build-log.md. Report summary and any ACTION REQUIRED."
  },
  "delivery": { "mode": "announce", "bestEffort": true }
}
```

`delivery.channel` og `delivery.to` kan sættes for at sende til et bestemt Telegram-chat/topic (fx `"channel": "telegram", "to": "-1001234567890"`).

---

## Noter

- **CET:** Bruger `Europe/Copenhagen` (sommer-/vintertid håndteres automatisk).
- **Isolated:** Hver run er en frisk session; ingen carry-over fra main chat.
- **Announce:** Kort summary postes til chat efter run; hvis du vil undgå det, brug `--delivery none` (eller `delivery.mode: "none"`).

*Se også: https://docs.openclaw.ai/automation/cron-jobs*
