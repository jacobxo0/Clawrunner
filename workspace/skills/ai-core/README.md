# AI-CORE Skill

Denne skill giver agent-turns adgang til AI-CORE's tool execution engine.

## Setup

1. Sæt `AI_CORE_URL` i Railway Variables (fx `https://ai-core-xxx.railway.app`)
2. Agenter kan nu kalde AI-CORE tools via HTTP POST til `${AI_CORE_URL}/command`

## Brug i agent-prompts

Inkludér denne linje i din agent-prompt for at give adgang til AI-CORE:

```
Before running system checks, call POST ${AI_CORE_URL}/command with {"command":"healthcheck","arguments":{}} and verify success:true.
```

Eller for system info:
```
Get system metrics by calling POST ${AI_CORE_URL}/command with {"command":"system_info","arguments":{}}.
```

## Se: workspace/agents/ai-core/AI_CORE_TOOLS.md

Fuld dokumentation af alle tools og argumenter.
