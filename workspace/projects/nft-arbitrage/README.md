# NFT Arbitrage → Commodity Arbitrage Pivot

This is a working copy of the original NFT Arbitrage system (copied from `D:\NFT Arbitrage` on 2026-02-22). We will use it as the foundation for the new commodity (precious metals / gemstones) arbitrage platform.

## Current State
- Full stack app (FastAPI backend + React/Next frontend)
- Ingestion modules for OpenSea / LooksRare / Blur
- Scoring/alert system with Postgres/SQLite DB and Alembic migrations
- Docker-compose + scripts for workers and schedulers
- Database snapshot: `nft_arbitrage.db`

## Pivot Plan
1. **Research Agent validation (phase 0)**
   - Collect sources for metals/gemstone arbitrage
   - Validate feasibility, scams, logistics, regulations
   - Output: GO/NO-GO + adjustments/extra hires required
2. **Engine Agent work**
   - Replace NFT ingestors with commodity data sources
   - Update scoring model to include fees, logistics, assay, etc.
   - Adapt frontend dashboards to commodities
3. **Growth Agent**
   - Messaging, funnels, distribution plan
4. **Ops Agent**
   - Reporting, monitoring, cron jobs

## Scripts
- (to do) `scripts/run_dev.ps1` – spins up virtualenv/docker
- (to do) `scripts/run_backend.ps1`
- (to do) `scripts/run_frontend.ps1`

## Next Steps
- [ ] Add Research Agent prompt + script
- [ ] Run Research Agent for metals/gemstone feasibility (gatekeeper)
- [ ] Document findings in `reports/`
- [ ] Update plan based on research outcome
