# TIPS / ECB SCT Inst samples

## References
- **TARGET Instant Payment Settlement (TIPS) – UDFS v12.0 (Annex 6: ISO 20022 message samples)**  
  - URL: https://www.ecb.europa.eu/paym/target/tips/professionals/html/index.en.html  
  - Contains pacs.008 and camt.056 XML fragments for SCT Inst settlement flows.  
  - Storage plan: mirror Annex 6 XML snippets into `datasets/raw/ecb/` with filename convention `tips-{message}-{version}.xml`.
- **TARGET Services – ISO 20022 message guidelines (2024-11)**  
  - URL: https://www.ecb.europa.eu/paym/target/shared/pdf/guidelines_iso20022_message.pdf  
  - Provides canonical field-level descriptions used for validation; good for schema cross-checks.

## Notes
- ECB sample payloads are explicitly labelled as illustrative; safe to include verbatim.  
- Need to document any edits (e.g., redacted BICs) inside each XML file header comment.  
- Next step: automate download via `scripts/fetch_tips_samples.py` once repo scaffolding is ready.
