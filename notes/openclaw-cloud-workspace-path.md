# OpenClaw på cloud: workspace-sti i openclaw.json

På VPS skal `agents.defaults.workspace` pege på den **Linux-sti** hvor workspace-mappen ligger.

## Eksempel

- **Windows (lokalt):** `C:\\Users\\Jnkri\\.openclaw\\workspace`
- **Linux (VPS, bruger ubuntu):** `/home/ubuntu/openclaw/workspace`

I `openclaw.json` på VPS, under `agents.defaults`, sæt:

```json
"workspace": "/home/ubuntu/openclaw/workspace"
```

(Erstatt `ubuntu` med den bruger du kører under, og `/home/ubuntu/openclaw` med den mappe hvor du har kopieret OpenClaw-filerne.)

OpenClaw læser config typisk fra `~/.openclaw/openclaw.json` eller fra den mappe hvor du kører gatewayen, afhængigt af hvordan du har sat det op. Sørg for at den `openclaw.json` der læses på VPS har den korrekte `workspace`-sti.
