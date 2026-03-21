# Build Log

## 2026-02-23 21:01 CET
- Documented stack choices in `notes/stack-selection.md` (Redpanda + FastAPI + Postgres/pgvector + LangGraph + React/Vite).
- Marked Stack selection items as complete on Phase 0 board.
- Created agent prompt files and run scripts under `agents/instant-mesh/` and `scripts/` to enable autonomous runs (BuildConductor, DatasetCrafter, InvestorScout, StatusWeaver).
- Initialized logging folder (`logs/`) and status board scaffolding.

**Requests / Blockers**
- Need approval to start repo scaffolding + dataset acquisition scripts.
- Need confirmation before enabling cron jobs for automated agent runs.

## 2026-02-28 21:10 CET
- Added ECB/EPC SCT Inst sample payloads under datasets/raw and documented TIPS sources.
- Created synthetic stream generator (Python) plus scenario catalog README.
- Defined minimum demo dataset spec covering 50k events with 5% flagged scenarios.

**Files touched**
- datasets/raw/ecb-pacs008-sample.xml
- datasets/raw/epc-pacs008-sample.xml
- datasets/sources/tips.md
- datasets/generator/README.md
- datasets/generator/synthetic_stream_generator.py
- datasets/minimum-demo-dataset.md
- notes/phase0-tasks.md

**Requests / Blockers**
- Need approval to mirror EPC/ECB PDFs directly into repo or prefer link-only references?
- Awaiting go-ahead to scaffold mono-repo + automation scripts (unchanged).

## 2026-03-01 08:34 CET
- **Repo & CI setup – DONE.** Created mono-repo scaffold under `repo/`:
  - `backend/` – pyproject.toml (Python 3.12, FastAPI, asyncpg, pgvector, confluent-kafka, duckdb), app entry point + health endpoint + smoke test
  - `agents/`, `ui/` – placeholder dirs
  - `infra/compose.redpanda.yml` – Redpanda + pgvector/Postgres dev stack
  - `.env.example`, `.pre-commit-config.yaml` (ruff + mypy + hooks), `justfile` task runner, `README.md`
- **Schema definition – DONE.** Created Pydantic v2 schemas:
  - `schemas/iso20022_subset.py` – Pacs008Extract, Camt056Extract, Acmt023Extract (key field extractions)
  - `schemas/events.py` – NormalizedEvent + RiskScore (canonical internal pipeline format)
  - `schemas/cases.py` – Case + CaseNote + enums for status/priority (agent handoff format)
- **Investor prep kickoff – confirmed complete** (target-list, deck-outline, memo-outline already existed from prior sessions). Checked off.
- **Phase 0 fully complete.** All 15 taskboard items checked off.

**Files created/touched**
- `repo/` – entire scaffold (12 files)
- `repo/backend/app/schemas/` – 4 files (iso20022_subset, events, cases, __init__)
- `notes/phase0-tasks.md` – all boxes checked, Phase 0 marked complete

**Requests / Blockers**
- ACTION REQUIRED: Phase 0 is done. Jacob needs to approve moving to **Phase 1 (Streaming core)** – ISO 20022 ingestion, baseline rules engine, audit log.
- Previous open Q still pending: mirror EPC/ECB PDFs into repo or keep as link-only references?

## 2026-03-02 08:05 CET
- Reconciled the dataset work-plan doc with the artifacts delivered (raw XML samples, generator, schema references) so Phase 0 evidence is self-contained.
- Highlighted where the canonical event schema and scenario catalog live to smooth future reviews + onboarding.
- Re-validated Phase 0 completion state; Phase 1 kickoff is still waiting on approvals listed below.

**Files touched**
- datasets/README.md

**Requests / Blockers**
- ACTION REQUIRED: Approve the transition to Phase 1 (streaming core build).
- ACTION REQUIRED: Decide whether EPC/ECB PDFs can be mirrored inside the repo (ECB Annex 6 samples are illustrative; EPC Appendix A still needs approval).
- ACTION REQUIRED: Confirm final fundraise target + whether to draft the investor teaser/email template now.

## 2026-03-03 08:00 CET
- Compiled Phase 1 kickoff readiness note capturing completed Phase 0 deliverables, open approvals, and initial scope proposal.
- Reiterated outstanding decisions (phase transition, ISO doc mirroring, investor messaging scope) to unblock next phase.

**Files touched**
- notes/phase1-kickoff-ready.md

**Requests / Blockers**
- ACTION REQUIRED: Approve Phase 0 → Phase 1 transition so streaming-core tickets can be cut.
- ACTION REQUIRED: Decide whether EPC/ECB guideline PDFs can be mirrored in-repo or must stay link-only.
- ACTION REQUIRED: Confirm investor raise target + whether to draft teaser email template ahead of Phase 1 demo.

## 2026-03-04 16:56 CET
- Captured Phase 1 telemetry/logging plan plus dev resource footprint so stack choices don’t stall once approvals drop.
- Drafted quantitative exit metrics (throughput, latency, determinism, rules accuracy, audit completeness) to lock acceptance criteria for the streaming core.

**Files touched**
- notes/phase1-telemetry-and-metrics.md

**Requests / Blockers**
- ACTION REQUIRED: Approve Phase 0 → Phase 1 transition so streaming-core tickets can be cut.
- ACTION REQUIRED: Decide whether EPC/ECB guideline PDFs can be mirrored in-repo or must stay link-only.
- ACTION REQUIRED: Confirm investor raise target + whether to draft teaser email template ahead of Phase 1 demo.

## 2026-03-05 08:10 CET
- Drafted a Phase 1 streaming backlog (ingestion, normalization, rules, audit, telemetry) so tasks can be ticketized immediately after approvals.
- Captured gating decisions + dependencies inside the backlog to keep the approval queue explicit.

**Files touched**
- notes/phase1-streaming-backlog.md

**Requests / Blockers**
- ACTION REQUIRED: Approve Phase 0 → Phase 1 transition so streaming-core tickets can be cut.
- ACTION REQUIRED: Decide whether EPC/ECB guideline PDFs can be mirrored in-repo or must stay link-only (affects ingestion fixtures).
- ACTION REQUIRED: Confirm final raise target, dilution guardrails, and whether to draft the investor teaser/email template now.
- ACTION REQUIRED: Approve design-partner PSP shortlist + assign intro owners so telemetry/demo story stays aligned with outreach.
## 2026-03-06 13:45 CET
- Compiled 
otes/phase0-evidence-pack.md so Jacob can review every Phase 0 deliverable in one place before issuing the Phase 1 GO.
- Re-validated that 
otes/phase0-tasks.md remains fully checked and aligned with the evidence pack; no hidden blockers discovered.

**Files touched**
- notes/phase0-evidence-pack.md
- logs/build-log.md

**Requests / Blockers**
- ACTION REQUIRED: Approve the Phase 0 ? Phase 1 transition so streaming-core tickets can be cut.
- ACTION REQUIRED: Decide whether EPC/ECB guideline PDFs can be mirrored inside the repo (impacts ingestion fixtures + docs).
- ACTION REQUIRED: Confirm final raise target, dilution guardrails, and whether to draft the investor teaser/email template now.
- ACTION REQUIRED: Approve the design-partner PSP shortlist + assign intro owners to keep telemetry/demo narratives aligned.
## 2026-03-06 21:06 CET
- Created 
otes/phase0-signoff-checklist.md consolidating every Phase 0 deliverable + evidence so Jacob can issue GO quickly.
- Updated status-board.md (Completed column) to reflect the new sign-off checklist artefact for transparency.

**Files touched**
- notes/phase0-signoff-checklist.md
- status-board.md

**Requests / Blockers**
- ACTION REQUIRED: Approve the Phase 0 ? Phase 1 transition so streaming-core tickets can be cut.
- ACTION REQUIRED: Decide whether EPC/ECB guideline PDFs can be mirrored inside the repo (impacts ingestion fixtures + docs).
- ACTION REQUIRED: Confirm final raise target, dilution guardrails, and whether to draft the investor teaser/email template now.
- ACTION REQUIRED: Approve the design-partner PSP shortlist + assign intro owners to keep telemetry/demo narratives aligned.

## 2026-03-07 11:55 CET
- Re-reviewed Phase 0 taskboard + sign-off checklist; no drift or regressions detected.
- Updated phase0-signoff-checklist.md purpose note and status-board timestamp to document the 2026-03-07 validation pass.
- Reiterated outstanding approvals so Phase 1 can start immediately once Jacob gives the GO.

**Files touched**
- notes/phase0-signoff-checklist.md
- status-board.md

**Requests / Blockers**
- ACTION REQUIRED: Approve the transition to Phase 1 so streaming-core tickets can be cut and telemetry backlog can launch.
- ACTION REQUIRED: Decide whether EPC/ECB guideline PDFs can be mirrored inside the repo or must stay link-only (impacts ingestion fixtures + docs).
- ACTION REQUIRED: Confirm final seed raise target, acceptable dilution band, and whether to prep the investor teaser/email template now.
- ACTION REQUIRED: Approve/adjust the design-partner PSP shortlist (Enfuce, Banking Circle, ClearBank) and assign intro owners.
- ACTION REQUIRED: Provide warm intro owners for Northzone, EQT Ventures, and the remaining top-13 investors, plus approve canonical data sources + certification budget/hiring cost bands for investor materials.

## 2026-03-08 11:29 CET
- Packaged the outstanding approvals into 
otes/phase1-approval-brief.md so the Phase 1 GO can happen without hunting through prior notes.
- Revalidated that Phase 0 artefacts remain aligned with the evidence pack; no new build work can start until approvals land.

**Files touched**
- notes/phase1-approval-brief.md

**Requests / Blockers**
- ACTION REQUIRED: Approve the Phase 0 ? Phase 1 transition so streaming-core tickets can be executed.
- ACTION REQUIRED: Decide whether ECB/EPC guideline PDFs may be mirrored inside the repo (preferred for offline fixtures) or must stay link-only.
- ACTION REQUIRED: Confirm final raise target, acceptable dilution band, and whether to draft the investor teaser/email template now.
- ACTION REQUIRED: Approve/adjust the design-partner PSP shortlist (Enfuce, Banking Circle, ClearBank) and assign intro owners.
- ACTION REQUIRED: Provide warm intro owners for Northzone, EQT Ventures, and the remaining top investors, plus approve canonical data sources + certification budgets for investor materials.
## 2026-03-09 08:00 CET
- Re-ran BuildConductor checkpoint; Phase 0 artefacts (evidence pack, sign-off checklist, approval brief) remain up-to-date with no regressions.
- Updated status-board.md timestamp and daily summary to show we are still waiting on approvals before starting any Phase 1 streaming work.

**Files touched**
- status-board.md

**Requests / Blockers**
- ACTION REQUIRED: Approve the Phase 0 ? Phase 1 transition so streaming-core tickets can be executed immediately.
- ACTION REQUIRED: Decide whether ECB/EPC guideline PDFs can be mirrored inside the repo or must stay link-only (impacts ingestion fixtures + docs).
- ACTION REQUIRED: Confirm final seed raise target, acceptable dilution band, and whether to draft the investor teaser/email template now.
- ACTION REQUIRED: Approve/adjust the design-partner PSP shortlist (Enfuce, Banking Circle, ClearBank) and assign intro owners.
- ACTION REQUIRED: Provide warm intro owners for Northzone, EQT Ventures, and the remaining top investors, plus approve canonical data sources + certification budgets for investor materials.
