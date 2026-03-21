# Dataset plan (Phase 0)

## Goals
- Have realistic ISO 20022 SCT Inst message samples for ingestion testing.
- Generate synthetic fraud scenarios (APP, mule, sanction hit) with labels for scoring evaluation.
- Ensure all data is synthetic or sourced from public documentation (no PII).

## Sources to evaluate
1. **ECB / TARGET Instant Payment Settlement (TIPS)** sample messages (public docs). Store links + notes in `sources/tips.md`.
2. **European Payments Council** ISO 20022 implementation guidelines – contains sample pacs.008 XML payloads (Appendix A). Download PDFs + extract XML snippets into `raw/epc/`.
3. **ISO 20022 sample repository** (e.g., `https://github.com/iso-20022/iso-20022-samples`). Mirror relevant pacs.008 / camt.056 examples.
4. **UK Pay.UK Confirmation of Payee sandbox** – provides mocked FPS instant payment flows we can translate to SCT Inst format.
5. **Custom generator** – script to create synthetic payer/payee data, amounts, timestamps, plus scenario labels.

## Work plan
- [x] Collect sample XML files and store under `datasets/raw/`.  
  - ✅ `raw/ecb-pacs008-sample.xml` (ECB TIPS Annex 6) and `raw/epc-pacs008-sample.xml` (EPC guideline Appendix A) captured with inline source notes.
- [x] Write generator (Python) producing JSON/CSV streams matching pacs.008 fields.  
  - ✅ `generator/synthetic_stream_generator.py` + README describing scenario knobs and output formats.
- [x] Define event schema mapping raw ISO messages to internal JSON used by scoring engine.  
  - ✅ Canonical schema lives in `repo/backend/app/schemas/events.py` (Phase 0 schema definition deliverable).
- [x] Curate scenario catalogue (legit payment, sanction hit, APP scam, mule network, velocity abuse).  
  - ✅ Scenario list + label definitions documented in `generator/README.md` and `datasets/minimum-demo-dataset.md`.
- [x] Document dataset specs for reuse in investor demos.  
  - ✅ `minimum-demo-dataset.md` covers volume, fraud rate targets, and refresh cadence for demo slices.
