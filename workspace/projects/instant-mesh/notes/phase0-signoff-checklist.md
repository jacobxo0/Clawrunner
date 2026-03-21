# Phase 0 Sign-off Checklist
_Last updated: 2026-03-07 11:55 CET_

Purpose: give Jacob a single-page confirmation that every Phase 0 deliverable is ready for approval, with links back to artefacts. Reviewed on 2026-03-07 to reconfirm all artefacts remain unchanged and ready for sign-off.

## Checklist summary
| Track | Deliverable | Evidence | Notes | Status |
| --- | --- | --- | --- | --- |
| Dataset plan | Public ISO 20022 SCT Inst samples captured | `datasets/raw/*pacs008*.xml`, `datasets/README.md` | ECB/EPC sources cited with provenance notes | ✅ Done |
| Dataset plan | Synthetic generator + labelled scenarios | `datasets/generator/README.md`, `datasets/generator/synthetic_stream_generator.py` | Emits JSON/CSV with checksum + fraud tags | ✅ Done |
| Dataset plan | Minimum demo dataset spec | `datasets/minimum-demo-dataset.md` | 50k txn / 5% fraud mix documented | ✅ Done |
| Stack selection | Event bus / services / state / agent choices | `notes/stack-selection.md` | Includes rationale + fallbacks | ✅ Done |
| Stack selection | Dev infra references | `repo/infra/compose.redpanda.yml`, `.env.example` | Boots Redpanda + Postgres stack locally | ✅ Done |
| Repo & CI setup | Mono-repo scaffold + lint/test hooks | `repo/` tree, `.pre-commit-config.yaml`, `justfile` | Poetry + pytest + hooks configured | ✅ Done |
| Schema definition | ISO subsets + normalized events + cases | `repo/backend/app/schemas/*.py` | Pydantic v2 models with audit metadata | ✅ Done |
| Investor prep | Target list + deck outline + memo outline | `investor/*.md` | Target investors + messaging scaffolds ready | ✅ Done |
| Evidence aggregation | Phase 0 evidence pack | `notes/phase0-evidence-pack.md` | Reference map for reviewers | ✅ Done |

## Outstanding approvals required from Jacob
1. **Phase transition:** Explicit GO to start Phase 1 streaming-core build.
2. **Reference policy:** Whether EPC/ECB guideline PDFs can be mirrored inside the repo or must stay link-only.
3. **Investor envelope:** Final raise target, dilution guardrails, and decision on prepping teaser/email template now.
4. **Design partners:** Approve PSP shortlist (Enfuce, Banking Circle, ClearBank) and assign intro owners.

Everything above is ready; once the four approvals land, the Phase 1 backlog (`notes/phase1-streaming-backlog.md`) can be burst into tickets immediately.
