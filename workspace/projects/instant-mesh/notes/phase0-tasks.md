# Phase 0 taskboard (draft)

## Dataset plan
- [x] Collect public ISO 20022 SCT Inst sample messages (ECB, EPC documentation).
- [x] Generate synthetic instant-payment streams with labelled fraud/scenario tags.
- [x] Define minimum dataset for demo (e.g., 50k transactions, 1% flagged).

## Stack selection
- [x] Event bus: Redpanda (self-hosted) vs. Kafka; evaluate dev experience.
- [x] Services: Python/FastAPI for scoring? Rust/Go for low latency? Document tradeoffs.
- [x] State store: Postgres + DuckDB for analytics; vector store (pgvector) for embeddings.
- [x] Agent layer: Autogen vs. LangGraph; choose with reasoning.

## Repo & CI setup
- [x] Create mono-repo structure (`backend/`, `agents/`, `ui/`, `infra/`).
- [x] Configure Poetry/UV (Python) + Rust/Cargo if needed; set lint/test pipelines.
- [x] Add pre-commit hooks, formatting rules, and example `.env`.

## Schema definition
- [x] ISO 20022 message subset mapping (pacs.008, camt.056, acmt.023).
- [x] Internal normalized event schema (JSON) for scoring pipeline.
- [x] Case/alert object schema for agent handoff.

## Investor prep kickoff
- [x] Build spreadsheet of target funds/angels + intro paths.
- [x] Draft deck outline (slide list + key data points needed).
- [x] Draft 2-page memo outline (problem, solution, market, go-to-market, funding ask).

*Progress will be updated here after each work session.*

---
**✅ Phase 0 complete.** All tasks checked off as of 2026-03-01. Ready for Phase 1.
