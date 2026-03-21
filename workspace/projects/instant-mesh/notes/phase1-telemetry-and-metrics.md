# Phase 1 telemetry, resource footprint, and success metrics

_Last updated: 2026-03-04 16:55 CET_

## Dev resource footprint (Docker Compose baseline)
- **Redpanda**: constrained to `--smp 1` and `--memory 512M` per `repo/infra/compose.redpanda.yml`; recommend reserving ~1 vCPU and 1 GB RAM on developer laptops to cover broker + rpk health checks.
- **Postgres + pgvector**: default image footprint peaks around 512 MB RAM during replay tests; reserve 1 vCPU and 1.5 GB RAM to leave headroom for pgvector index creation and audit-log bursts.
- **Overall**: keep at least 4 GB RAM free before launching the stack; `docker stats` target envelope = <2.5 GB combined usage so ingestion/rules services can run locally without swapping.
- **Disk**: allocate 5 GB for persistent `pgdata` volume (retains replay artifacts + pgvector embeddings once ML prototypes start).

## Telemetry & logging approach (Phase 1 scope)
1. **Structured logging default**: use `structlog` + standard FastAPI logging config to emit JSON logs with `event_id`, `payment_id`, `rule_id`, and `case_id` fields. Ship to stdout for local dev and capture via Docker logging driver.
2. **Trace instrumentation**: adopt OpenTelemetry SDK (Python) with OTLP exporter pointed to the local collector (optional during Phase 1). Annotate spans for `ingest_pacs008`, `normalize_event`, `evaluate_rules`, and `persist_case` so latency budgets are visible once streaming benchmarks run.
3. **Metrics**: expose Prometheus-compatible metrics via FastAPI `/metrics` endpoint (leverage `prometheus-fastapi-instrumentator`). Key counters/gauges: `events_ingested_total`, `events_normalized_total`, `rule_evaluations_total`, `decision_latency_ms_bucket`, `audit_log_writes_total`.
4. **Log retention**: keep 7 days of structured logs locally (rotate via `loguru`/`structlog` handler). Longer retention will be defined when cloud env is introduced.

## Proposed Phase 1 exit metrics
| Domain | Metric | Target |
| --- | --- | --- |
| Throughput | Sustained ingestion of **1,000 events/sec** from synthetic pacs.008 replay without backlog growth. |
| Latency | p95 end-to-end (ingest → decision → audit write) **< 750 ms** for 1k TPS workload; p99 < 1.2 s. |
| Determinism | <0.1% replay variance when running the same synthetic batch twice (identical decision + audit outputs). |
| Rules accuracy | Synthetic scenarios ≥ **85% precision / 90% recall** relative to labeled fraud scenarios in generator catalog. |
| Audit completeness | 100% of high-risk decisions emit audit entries with rule_id, threshold, and normalization payload checksum. |
| Case bootstrap | 100% of risk scores above the configurable threshold create a Case object with link back to raw ISO message + normalized payload. |

## Next steps once approvals land
- Wire the telemetry defaults into `repo/backend/` service templates so new modules inherit structlog + OTEL config automatically.
- Script a `just stack:profile` helper to spin up Compose + run `docker stats --no-stream` checkpoints for documentation screenshots.
- Add benchmark harness in `repo/backend/tests/perf/` to validate throughput/latency targets before Phase 1 exit review.
