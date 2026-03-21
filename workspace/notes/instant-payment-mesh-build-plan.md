# Instant Payment Risk Mesh – build-first plan (draft)

*Status: Draft for Jacob's approval (do not execute until approved)*

## 1. MVP scope (internal labs build)
- **Realtime ingestion**: replay engine reading ISO 20022 SCT Inst messages (pacs.008 / camt.056) from sample datasets.
- **Risk scoring core**: rules + ML skeleton scoring each transaction on AML, sanctions, APP fraud likelihood.
- **Agentic workflow**: mock case bot that auto-populates an alert summary, sends to simulated investigator inbox.
- **Digital twin sandbox**: ability to replay historical batches with new rules, capture metrics.
- **Audit log**: append-only ledger of every decision.
- **UI**: Ops console showing live stream + alert queue (simple React/Vite or equivalent).

## 2. Architecture sketch
- Event bus (Kafka/Redpanda) -> scoring services (Python/FastAPI or Rust micro) -> state store (Postgres + vector store for embeddings) -> Agent service (Langchain/Autogen) -> UI & reporting.
- Modular adapters so we can later drop into real PSP feeds.

## 3. Build phases
1. **Phase 0 (Week 0-2)**: finalize datasets, choose stack, set up repo/CI, define message schemas.
2. **Phase 1 (Week 3-8)**: streaming ingestion + baseline rules engine + audit log.
3. **Phase 2 (Week 9-14)**: ML enrichment (graph features, device signals) + agentic case bot.
4. **Phase 3 (Week 15-20)**: digital twin + UI polish + documentation ready for demo.
5. **Phase 4 (Week 21+)**: investor demo package, synthetic data runs, performance metrics.

## 4. Resource assumptions
- Initial build driven by me (Ignis) + automation; heavy lifting via codegen/reusable scripts.
- For advanced ML modules we might spec requirements but keep them stubbed until we hire/partner.

## 5. Next action (requires Jacob approval)
- Spin up repo structure under `projects/instant-mesh/`.
- Draft detailed task list + assign owners (likely self until further notice).
- Begin Phase 0 tasks.

---

# Investor outreach plan (draft)

## A. Positioning question bank
- Problem framing: regulatory deadline 2025/26, PSP compliance gap, APP fraud cost.
- Solution proof: demo metrics from internal MVP (alert reduction %, detection latency).
- Business model: tiered ACV, managed detection upsell.

## B. Investor target list (initial)
- EU fintech/security-focused seed funds (e.g., byFounders, Seedcamp, Point Nine).
- Regtech angels/former compliance execs.
- Strategic PSP partners with venture arms.

## C. Materials needed
1. 10-slide deck (problem, solution, market, traction plan, financials).
2. 2-page memo summarizing regulation urgency + product edge.
3. Demo video or clickable prototype snippet from Phase 2/3 output.

## D. Outreach process
1. Build warm-intro map (who in network can intro to target funds/angels?).
2. Draft outreach emails + data room checklist.
3. Run “soft-sounding” conversations during Phase 2 (while MVP still internal) to line up interest.

## E. Funding strategy
- Target raise: €3–4m seed to hire team + certify solution.
- Terms: Only form NewCo when lead investor issues term sheet.
- Jacob retains majority; service agreements drafted post-term-sheet.

## F. Next action (requires Jacob approval)
- Flesh out investor target spreadsheet + intro notes.
- Draft deck outline (no external sharing yet).

---
*Nothing from the above will be executed before Jacob explicitly approves each next action.*