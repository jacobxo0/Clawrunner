# Phase 0 Evidence Pack
_Last updated: 2026-03-06 13:45 CET_

This note aggregates the artefacts proving that every Phase 0 checkpoint is complete and ready for Jacob's approval.

## 1. Dataset plan
- ✅ **Public ISO 20022 samples captured.** `datasets/raw/ecb-pacs008-sample.xml` (ECB TIPS Annex 6) and `datasets/raw/epc-pacs008-sample.xml` (EPC guideline Appendix A) referenced in `datasets/README.md` with source notes.
- ✅ **Synthetic generator + scenario labels.** `datasets/generator/synthetic_stream_generator.py` + accompanying `datasets/generator/README.md` produce JSON/CSV streams mapped to scenario IDs, with checksum + fraud tag outputs.
- ✅ **Minimum demo dataset spec.** `datasets/minimum-demo-dataset.md` defines 50k txn / 5% fraud slice, refresh cadence, and scenario mix for demos/investor proofs.
- ✅ **Schema linkage.** Dataset README links to `repo/backend/app/schemas/events.py` so ingestion + scoring work reuse the same canonical JSON representation.

## 2. Stack selection
- ✅ **Decisions documented.** `notes/stack-selection.md` locks Redpanda + FastAPI + Postgres/pgvector + LangGraph + React/Vite, with rationale and fallbacks.
- ✅ **Infra references ready.** `repo/infra/compose.redpanda.yml` boots Redpanda + Postgres dev stack in one command, aligning with the event bus/state store decision.
- ✅ **Tooling + lint standards.** Root `repo/justfile`, `.pre-commit-config.yaml`, and `.env.example` reflect the stack choices and enforce lint/test parity across dev machines.

## 3. Repo & CI setup
- ✅ **Mono-repo scaffolding.** `repo/backend/`, `repo/agents/`, `repo/ui/`, and `repo/infra/` exist with placeholder init files so downstream work can branch cleanly.
- ✅ **Backend baseline.** `repo/backend/app/main.py` exposes FastAPI health checks, and `repo/backend/tests/test_health.py` provides the first pytest smoke test wired via Poetry (see `repo/backend/pyproject.toml`).
- ✅ **Automation hooks.** `.pre-commit-config.yaml` (ruff + mypy) and `justfile` (lint/test/devstack helpers) are committed for consistent CI once remote runners are attached.

## 4. Schema definition
- ✅ **ISO subset extractors.** `repo/backend/app/schemas/iso20022_subset.py` captures pacs.008, camt.056, acmt.023 slices relevant to instant payments.
- ✅ **Normalized event contract.** `repo/backend/app/schemas/events.py` defines the canonical `NormalizedEvent` + `RiskScore` objects with audit metadata fields.
- ✅ **Case handoff schema.** `repo/backend/app/schemas/cases.py` models cases, notes, status enums, and priority controls for downstream agent/UI flows.

## 5. Investor prep kickoff
- ✅ **Target intelligence.** `investor/target-list.md` enumerates funds/angels, theses, and intro paths.
- ✅ **Deck skeleton.** `investor/deck-outline.md` lists slide narrative + data requirements so design work can start instantly.
- ✅ **Memo outline.** `investor/memo-outline.md` captures the 2-page brief structure, referencing the same metrics as the deck.
- ✅ **Status tracker.** `investor/status.md` summarizes artefacts delivered, open inputs, and next deliverables for InvestorScout runs.

## Outstanding approvals (unchanged)
1. **Phase transition:** Need explicit GO to start Phase 1 tickets (ingestion → audit build).
2. **Reference policy:** Decide if EPC/ECB PDFs can be mirrored inside the repo or must stay link-only (affects data fixture completeness).
3. **Investor envelope:** Provide final raise target + dilution guardrails + whether to draft the teaser email template now.
4. **Design partner shortlist:** Approve PSP targets + intro-owner mapping to align telemetry narratives with outreach.

Once these approvals land, Phase 1 backlog (`notes/phase1-streaming-backlog.md`) can be ticketized without rework.