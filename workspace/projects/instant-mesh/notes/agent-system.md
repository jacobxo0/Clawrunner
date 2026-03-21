# Instant Mesh Agent System (draft)

**Goal:** Run the build + investor workstreams autonomously and only ping Jacob with status snapshots / approvals.

**Overordnet ramme:** Alle agenter følger CORE-F (Comprehend → Orchestrate → Respond → Evaluate → Fine-tune). Se `notes/agent-system.md` i OpenClaw-roden for den fælles agent-model og prompt-hacks.

## Core agents

| Agent | Scope | Trigger | Output |
| --- | --- | --- | --- |
| **BuildConductor** | Owns Phase 0–3 technical work (datasets, stack, ingestion, scoring, UI). | Cron daily at 08:00 CET (can be muted). | `build-log.md` updates + TODO status. |
| **DatasetCrafter** | Generates/curates ISO 20022 samples & synthetic fraud data, maintains schema docs. | Spawned by BuildConductor when dataset checklist not green. | Updated files under `datasets/` + validation notes. |
| **InvestorScout** | Maintains target list, drafts deck/memo, prepares outreach packages (no sends). | Cron Mon/Wed 10:00 CET. | `investor/status.md` snapshot + deck/memo diffs. |
| **StatusWeaver** | Aggregates progress from sub-agents, posts short chat summary + optional visual board. | Runs after any agent finishes OR nightly 20:00 CET. | Message to Jacob + updated `status-board.md`. |

## Execution flow
1. **Scheduler (cron)** kicks BuildConductor + InvestorScout per cadence.  
2. Each agent works inside project repo, writes logs/artifacts, and marks tasks in `phase0-tasks.md`.  
3. On completion, agent notifies StatusWeaver which compiles a short summary + visual board (Mermaid Kanban) and posts to chat.  
4. Any action requiring approval is flagged in summary (e.g., "Need GO to start outreach").

## Automation hooks
- Use `sessions_spawn` with prompts stored under `agents/instant-mesh/` (to be created) for BuildConductor & InvestorScout.  
- Cron jobs (gateway) schedule:
  - `instant-mesh-build` → daily 08:00 CET, sessionTarget=isolated, runs BuildConductor prompt.  
  - `instant-mesh-investor` → Mon/Wed 10:00 CET.  
  - `instant-mesh-status` → daily 20:00 CET to summarize `build-log.md` + `investor/status.md`.

## Next steps
1. Draft agent prompt files (BuildConductor, DatasetCrafter, InvestorScout, StatusWeaver).  
2. Create logging structure (`logs/build-log.md`, `logs/investor-log.md`, `status-board.md`).  
3. Dry-run BuildConductor manually (sessions_spawn) to ensure instructions work.  
4. Once stable, register cron jobs so system runs autonomously.  

*Blocking actions (cron setup, actual agent runs) will only happen after Jacob approves this plan.*