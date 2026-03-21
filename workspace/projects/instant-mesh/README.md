# Instant Payment Risk Mesh – Build & Investor Workstream

**Owner:** Ignis (reports to Jacob)  
**Status:** Phase 0 (setup)  
**Last updated:** 2026-02-23

## Objectives
1. Build an internal MVP/PoC of the Instant Payment Risk Mesh without forming a company yet.  
2. In parallel, prepare investor-facing materials so we can trigger a raise the moment there is interest.  
3. Keep every step documented and gated by Jacob’s approval.

## Phase breakdown
| Phase | Scope | Target duration | Notes |
| --- | --- | --- | --- |
| 0. Foundations | Datasets, stack decisions, repo/CI scaffolding, message schemas | Weeks 0-2 | Internal only |
| 1. Streaming core | ISO 20022 ingestion, baseline rules engine, audit log | Weeks 3-8 | Synthetic data |
| 2. ML & agents | Graph/feature enrichment, case-bot skeleton | Weeks 9-14 | No production data |
| 3. Twin + UI | Replay sandbox, operator console, docs | Weeks 15-20 | Demo-ready |
| 4. Investor pack | Deck, memo, demo video, target list | Weeks 21+ | For fundraising |

## Immediate tasks (Phase 0)
1. **Dataset plan** – identify synthetic/opensource SCT Inst samples + fraud scenarios.  
2. **Stack selection** – lock choices for event bus, services, storage, infra.  
3. **Repo setup** – create mono-repo with backend, agent, ui packages; configure lint/tests.  
4. **Schema definition** – capture ISO 20022 message subsets and internal event format.  
5. **Investor prep kickoff** – list target funds/angels + outline deck/memo structure.

Progress on these tasks will be logged in `notes/` and subdirectories inside this project.

## Communication rules
- No external outreach, contracts, or company formation happens without explicit “GO” from Jacob.  
- Status snapshots live in `notes/instant-payment-mesh-status.md` and this project README.  
- Every major artifact (architecture diagrams, deck drafts, code scaffolds) will be stored under `projects/instant-mesh/` and referenced in updates.
