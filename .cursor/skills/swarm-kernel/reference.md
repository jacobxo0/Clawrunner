# Swarm Kernel — Reference

Detailed definitions and escalation guidance. Use when enforcing state transitions, diagnosing loops, or escalating to capability architect.

## Work Unit States

| State | Meaning |
|-------|---------|
| `NEW` | Task or unit received, not yet planned |
| `PLANNED` | Broken into work units with objectives and verification |
| `IN_PROGRESS` | Currently being executed or fixed |
| `QC_FAILED` | QC rejected; needs repair |
| `FIXING` | Fixer is addressing QC failure |
| `QC_PASSED` | QC approved; eligible for integration |
| `INTEGRATED` | Combined into system; awaiting regression |
| `REGRESSION_FAILED` | Regression QC failed; needs fix and re-check |
| `DONE` | Release Gate approved; task complete |
| `BLOCKED` | Blocked by external factor (credentials, decision, etc.) |

Valid transitions follow routing discipline: e.g. Executor output → QC (not → DONE). Do not allow ambiguous or made-up statuses.

## Anti-Chaos — Full List

The kernel must prevent:

1. **Giant undivided tasks** — Split before execution.
2. **Debate without output** — Require verifiable artifacts, not only discussion.
3. **Retries without strategy change** — After repeated failure, narrow scope or change approach.
4. **Direct completion from implementation** — No Executor → Done; always via QC and Release Gate.
5. **Self-approval** — Executor/Fixer/Integrator do not approve their own work.
6. **Skipped regression** — Integrated work must pass Regression QC.
7. **Unexplained role switching** — Transitions must match the defined flow and be justified.

## Capability Escalation — Triggers and Wording

Escalate to the capability architect when:

- The same QC failure pattern appears on multiple units or runs.
- The same task type repeatedly needs ad-hoc handling.
- The same routing mistake or bypass recurs.
- One role is consistently overloaded or underused.
- A single new skill or convention would clearly reduce failure or rework.

Example escalation note:

> **Capability escalation:** [Pattern observed]. Occurred [N] times. Suggests [missing structure / overloaded role / missing skill]. Recommend [concrete suggestion if any].

Keep escalation factual and evidence-based; do not escalate on a single occurrence unless it indicates a structural gap.

---

## Learned Anti-Patterns (Do Not Repeat)

These were observed in practice; the swarm must not repeat them.

1. **Handing off terminal/ops work to the user**  
   The agent must run terminal work itself (gateway start, cron list, run_cycle, pip, scripts). Do not respond with "run this command in your terminal" unless the action truly requires the user (e.g. password, physical device). If the project has a `run-terminal-tasks` or equivalent script, the agent runs it.

2. **Delivering new work without deploying**  
   When the agent produces new or updated artifacts (code, config, cron, docs) that are intended for a live environment (Railway, VPS, or shared repo), it must deploy: commit and push (and, if applicable, run upload/VPS or trigger deploy). Do not leave "push when you're ready" to the user when the agent can do it. Completion includes "deployed" when deployment is part of the task or project norm.

3. **Deploying without following build logs**  
   After a deploy (e.g. push to Railway), the agent must follow build/deploy outcome: run the project’s log-fetch script (e.g. `railway-logs-to-workspace.ps1`) if available, read the resulting log file, and fix any reported errors in the same turn. If the user shares build logs or a screenshot, use them to diagnose and fix. Do not consider deploy "done" until the build/runtime is known to succeed or the failure has been addressed.

When a mistake in this list is repeated, treat it as a routing/execution failure and correct it in the same turn; optionally add to this list if a new pattern is identified.
