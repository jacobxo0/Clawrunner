# Phase 1 streaming backlog (draft)

_Last updated: 2026-03-05 08:05 CET_

## Scope alignment
- **Goal:** Stand up the streaming core covering ISO 20022 ingestion → normalization → rules evaluation → audit/case write within the repo scaffolding delivered in Phase 0.
- **Exit guardrails:** Must satisfy the throughput/latency + audit metrics captured in `phase1-telemetry-and-metrics.md` before requesting sign-off.
- **Dependencies:** Phase 0 approvals to start, decision on mirroring ISO guideline PDFs, investor brief parameters (teaser + raise target) so messaging doesnt lag behind build progress.

## Workstream breakdown

### 1. ISO 20022 ingestion service (`repo/backend/app/ingest`)
- [ ] Scaffold FastAPI router + Kafka/Redpanda consumer with confluent-kafka wrapper.
- [ ] Implement pacs.008 replay worker reading from `datasets/generator` outputs (JSON/CSV) and publishing to Redpanda topic `iso.raw.pacs008`.
- [ ] Add CLI/`just ingest:replay` helper for deterministic batches + config file for replay cadence.
- [ ] Write integration test hitting Redpanda stub to confirm offsets/acks arent lost when 1k TPS load is applied.

### 2. Normalization & enrichment (`repo/backend/app/normalize`)
- [ ] Build transformer that maps ISO XML/JSON payloads into `NormalizedEvent` schema using existing Pydantic models.
- [ ] Include checksum + source metadata (doc reference, generator scenario id) to satisfy audit requirements.
- [ ] Publish normalized events to topic `iso.normalized.events` and persist to Postgres (jsonb + pgvector columns for later ML work).
- [ ] Unit test coverage for field-level mapping + schema drift detection.

### 3. Rules engine baseline (`repo/backend/app/rules`)
- [ ] Implement rules registry (YAML/JSON definitions) loaded at startup with hot-reload hook.
- [ ] Cover starter rule packs: velocity, geo/IBAN mismatch, sanction keyword heuristics, mule pattern (graph-lite), scenario expectation checks.
- [ ] Emit structured decisions with `rule_id`, `score`, `threshold`, `matched_features` per `schemas/events.py`.
- [ ] Provide quick benchmark harness referencing synthetic scenarios to tune thresholds before telemetry run.

### 4. Audit + case writer (`repo/backend/app/audit`)
- [ ] Persist every decision >= threshold into `cases` table using existing `Case` schema plus audit trail table capturing normalization payload checksum.
- [ ] Expose `/cases/{id}` API returning joined ISO raw + normalized event for operator review (will be reused by UI later).
- [ ] Wire Prometheus counters/gauges (events ingested, rules triggered, audit writes) tied to `prometheus-fastapi-instrumentator` plan.
- [ ] Define replay reconciliation script comparing consecutive batch outputs to enforce determinism target (<0.1% variance).

### 5. Telemetry + tooling glue
- [ ] Bake structlog + OTEL config into shared `logging.py` module and import across ingest/normalize/rules/audit packages.
- [ ] Add `just stack:profile` command to spin up Docker Compose + emit `docker stats` snapshot as doc artifact.
- [ ] Draft `tests/perf/test_streaming_core.py` skeleton running 1k TPS synthetic benchmark (pytest marker `perf`).
- [ ] Document how to collect metrics dashboards (Prometheus curl, OTEL traces) for the Phase 1 exit review packet.

## Gating decisions (cannot start until resolved)
1. **Phase approval:** Need explicit GO from Jacob to move from Phase 0 → Phase 1.
2. **Reference policy:** Confirm whether EPC/ECB guideline PDFs can live inside the repo (affects ingestion fixtures + docs).
3. **Investor envelope:** Provide final raise target + dilution guardrails + teaser/email scope so investor comms stay synced once Phase 1 progress accelerates.
4. **Design partner shortlist:** Approve PSP targets + intro owner mapping, since telemetry + demo narratives will reference them.

Once these are cleared, convert each checklist above into tracked tickets (e.g., `phase1-streaming-core-01` etc.) and tag owners/dates.
