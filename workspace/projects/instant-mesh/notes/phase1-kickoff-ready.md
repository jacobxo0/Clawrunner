# Phase 1 kickoff readiness (draft)

_Last updated: 2026-03-03 08:00 CET_

## Phase 0 deliverables in place
- **Dataset plan** – Raw SCT Inst XML samples captured (ECB + EPC); synthetic stream generator + scenario catalog + demo dataset spec linked under `datasets/`.
- **Stack selection** – Decisions locked (Redpanda event bus, FastAPI services, Postgres/pgvector + DuckDB state, LangGraph agent layer, React/Vite UI).
- **Repo & CI scaffold** – Mono-repo under `repo/` with backend FastAPI skeleton, schemas, infra compose file, lint/test setup (ruff, mypy, pytest smoke), `.env.example`, `justfile`, pre-commit hooks.
- **Schema definitions** – ISO 20022 subset extracts, normalized event schema, and case/alert schema implemented in `repo/backend/app/schemas/` and referenced by docs.
- **Investor prep kickoff** – Target list, deck outline, and memo outline completed (see `investor/` artefacts) so fundraising workstream can resume when Phase 1 artifacts land.

## Outstanding approvals / decisions
1. **Phase transition** – Need Jacob’s GO to move from Phase 0 → Phase 1 (Streaming core build: ISO 20022 ingestion, baseline rules engine, audit log service).
2. **Source mirroring** – Decide whether EPC/ECB ISO 20022 guideline PDFs should be mirrored inside the repo (`datasets/raw/docs/`) or referenced via links only.
3. **Investor messaging scope** – Confirm raise target + whether to draft teaser email template now or wait until Phase 1 demo components exist.

## Proposed Phase 1 starting stack
- **ISO 20022 ingestion service** (Python/FastAPI worker)
  - Implements XML → normalized event translation using existing schemas.
  - Streams events into Redpanda topics (`payments.raw`, `payments.normalized`).
- **Baseline rules engine**
  - Deterministic rules + scenario labels from synthetic generator.
  - Emits `risk_decisions` topic with score + reason codes for audit log.
- **Audit log + case bootstrap**
  - Persist normalized events + decisions to Postgres (pgvector for future embeddings).
  - Auto-create Case objects when scores exceed thresholds for downstream agent testing.
- **Test harness**
  - Replay synthetic datasets through ingestion + rules to validate determinism before ML work.

## Dependencies / prep work
- Verify Docker/Compose resources for Redpanda + Postgres stack (document resource footprint for laptop dev by Phase 1 Day 1).
- Lock telemetry/logging approach (OpenTelemetry vs. structured logging) to avoid refactors when rules engine ships.
- Define success metrics for Phase 1 exit (e.g., end-to-end synthetic replay latency, rules precision/recall targets, audit completeness checklist).

> ACTION REQUIRED: Approvals listed above are still open; once cleared, Phase 1 tickets can be drafted from the proposed scope.
