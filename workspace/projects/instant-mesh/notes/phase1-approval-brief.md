# Phase 1 approval brief

_Last updated: 2026-03-08 11:29 CET_

This note packages the open approvals gating the Phase 0 → Phase 1 transition so Jacob can issue a GO quickly. Each item links back to the deliverables already in place and spells out the recommendation/next step.

## 1. Phase 0 → Phase 1 transition
- **Status:** All Phase 0 artefacts are complete and catalogued (`notes/phase0-evidence-pack.md`, `notes/phase0-signoff-checklist.md`, dataset specs, schemas, repo scaffold, investor prep outlines).
- **Why it matters:** Streaming-core backlog (`notes/phase1-streaming-backlog.md`) plus telemetry plan (`notes/phase1-telemetry-and-metrics.md`) are ready but blocked on formal GO.
- **Recommendation:** Approve Phase 1 kickoff so ingestion, normalization, baseline rules, and audit logging tickets can be cut immediately.
- **Next steps once approved:**
  1. Instantiate the backlog items under `repo/backend/` + `infra/` per streaming plan.
  2. Spin up dev Redpanda/Postgres stack via `infra/compose.redpanda.yml` and wire the ISO ingestion stubs.

## 2. ISO guideline mirroring (ECB/EPC PDFs)
- **Status:** Raw XML samples + references live under `datasets/`, but official guideline PDFs (ECB Annex 6, EPC Appendix A) remain link-only pending approval.
- **Risk of staying link-only:** Reviewers/offline agents lose context when disconnected; automated parsing/fixtures cannot reference the canonical wording.
- **Option A – Mirror internally:** Store PDFs under `datasets/docs/` with attribution + source links (preferred for reproducibility). Requires confirmation that redistribution for internal build is acceptable.
- **Option B – Link-only:** Keep URLs only; add scripted downloader for dev environments (slower onboarding, no offline mode).
- **Recommendation:** Approve Option A for repo-internal mirrors restricted to the private workspace. If legal worries persist, allow mirrors in a private object store and script pulls.

## 3. Fundraise target + investor messaging scope
- **Status:** Target-fund spreadsheet + deck/memo outlines exist (Phase 0). Teaser email/template is pending final raise target and dilution guardrails.
- **Decision needed:** Confirm round size (e.g., €3–4M seed vs. €5M+ growth), desired dilution %, and whether to pre-draft the teaser copy now vs. post-demo.
- **Recommendation:** Lock the target + dilution so InvestorScout can draft teaser + update the memo to keep investor sequencing in sync with the Phase 1 build.

## 4. Design-partner PSP shortlist & intro owners
- **Status:** Shortlist proposed (Enfuce, Banking Circle, ClearBank) but awaiting approval + assigned intro owners.
- **Why it matters:** Phase 1 telemetry/metrics narrative references these PSPs for design-partner validation; delaying assignments slows outreach prep.
- **Recommendation:** Approve/adjust the shortlist and tag intro owners so outreach cadences can kick off parallel to the streaming build.

## 5. Investor intro coverage + data/cert budget approvals
- **Status:** Need warm intro owners for Northzone, EQT Ventures, and remaining top-13 investors. Also need approval for canonical data sources + certification budget/hiring band to share in investor materials.
- **Recommendation:** Provide owner mapping + budget ranges so InvestorScout can finalize the investor data room outline and prep diligence responses.

---
Once the above approvals are captured, BuildConductor can immediately pivot to executing the Phase 1 backlog without further blocking items. ACTION REQUIRED tags for each decision are maintained inside `logs/build-log.md` for StatusWeaver.
