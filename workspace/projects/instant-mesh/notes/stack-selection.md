# Stack Selection Notes (2026-02-23)

## Event bus
- **Preferred:** Redpanda (self-hosted in dev, managed SaaS later). Reasons: single binary, no ZooKeeper, easier local dev, Kafka API compatible.
- **Fallback:** Apache Kafka via Bitnami container if we need full OSS reference.
- **Action:** Draft docker-compose snippet for Redpanda in `infra/compose.redpanda.yml` during repo setup.

## Services / languages
- **Realtime scoring services:** Python 3.12 + FastAPI for speed of iteration, with optional Rust microservice later for hot path. Python integrates cleanly with AML/risk libraries.
- **Background workers:** Prefect or custom async tasks using Dramatiq/Celery; initial plan is to leverage FastAPI + background tasks to keep stack light.

## State store
- **Primary:** PostgreSQL 16 with pgvector extension for embeddings + JSONB for message storage.
- **Analytics:** DuckDB for ad-hoc replay metrics.
- **Audit log:** Append-only table in Postgres + Parquet export for regulators.

## Agent layer
- **Framework candidate:** LangGraph (built on top of LangChain) to orchestrate deterministic case bots.
- **Reasoning:** Supports tool-calling flows and can run locally. We'll start with LangGraph + OpenAI-compatible LLMs (Claude/GPT) via environment variables.

## UI
- React + Vite + shadcn/ui for fast prototyping. Communicates with FastAPI backend via REST/WebSocket for streaming alert feed.

## Infra & tooling
- Dev containers using VS Code + devcontainer.json.
- Task runner: `just` or `make`. Favor `just` for cross-platform commands.
- Testing: pytest, mypy, Ruff for linting.

## Open Questions
- Do we need Rust from day 1? -> Likely not; keep as future optimization.
- Should we adopt Temporal for workflow orchestration? -> Evaluate after MVP ingestion works.

*Next step:* create repo skeleton reflecting these choices.
