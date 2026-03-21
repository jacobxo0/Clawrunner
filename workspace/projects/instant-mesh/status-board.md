# Instant Payment Risk Mesh – Status Board

_Last updated: 2026-03-09 08:00 CET (Phase 1 approvals still pending; streaming core can start immediately once GO arrives)_

## Phase Overview
- **Current phase:** Phase 0 (Foundation) — ✅ deliverables packaged in `notes/phase0-evidence-pack.md`; all taskboard items validated and ready for sign-off.
- **Next phase:** Phase 1 (Streaming core) — approvals still pending for ISO 20022 ingestion, baseline rules engine, audit trail, telemetry, and demo instrumentation scope.
- **Today’s review (2026-03-09 08:00):** Re-ran BuildConductor checks; no new build work possible until approvals below are cleared, evidence pack + approval brief remain current.

```mermaid
kanban
    section Completed
        Stack selection + tooling bootstrap
        Dataset scaffolding, generator, and evidence reconciliation
        Repo & CI scaffold (backend + infra + lint/test harness)
        Canonical schemas (ISO extracts, events, cases)
        Investor prep kickoff (target list, deck + memo outlines v1.2)
        Phase 1 kickoff readiness note
        Phase 1 telemetry + metrics acceptance criteria draft
        Phase 1 streaming backlog with gating decisions + dependencies
        Phase 0 evidence pack + validation passes (Mar 6-7)
        Phase 0 sign-off checklist (single-page)
        Phase 1 approval brief consolidating outstanding decisions
    section In Review / Pending
        Phase 1 kickoff approval from Jacob
        Decision on mirroring EPC/ECB PDFs inside repo
        Finalize seed raise target + dilution guardrails + teaser/email scope
        Approve design-partner PSP shortlist (Enfuce, Banking Circle, ClearBank)
        Assign warm intro owners for Northzone + EQT Ventures (and top-13 list)
        Approve canonical data sources for APP fraud + EU PSP counts
        Provide certification budget + hiring cost bands for use-of-funds slide
```

### Blockers / Approvals
- **ACTION REQUIRED:** Approve the transition to Phase 1 so streaming-core tickets can be executed.
- **ACTION REQUIRED:** Decide whether EPC/ECB guideline PDFs can be mirrored inside the repo or must remain link-only (impacts ingestion fixtures + docs).
- **ACTION REQUIRED:** Confirm final seed raise target, acceptable dilution band, and whether to draft the investor teaser/email template now.
- **ACTION REQUIRED:** Approve/adjust the proposed design-partner PSP list (Enfuce, Banking Circle, ClearBank) and share existing relationships.
- **ACTION REQUIRED:** Provide warm intro owners for Northzone, EQT Ventures, and the remaining top-13 investors.
- **ACTION REQUIRED:** Approve canonical APP fraud + EU PSP data sources and share certification budget + hiring cost bands for the investor materials.
