# Instant Payment Risk Mesh

Real-time fraud scoring, agentic case handling, and digital twin sandbox for SCT Inst payments.

## Structure

```
backend/    – FastAPI scoring & API service
agents/     – LangGraph agent orchestration
ui/         – React + Vite operator console
infra/      – Docker Compose, IaC configs
```

## Quick Start

```bash
cp .env.example .env          # fill in secrets
just infra-up                 # start Redpanda + Postgres
just install                  # install Python deps
just test                     # run tests
just serve                    # start API on :8000
```

## Pre-commit

```bash
pip install pre-commit
pre-commit install
```
