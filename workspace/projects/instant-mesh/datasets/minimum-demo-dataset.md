# Minimum demo dataset spec

- **Size:** 50,000 instant payment events (JSONL) covering 24h synthetic window.
- **Currency mix:** 70% EUR, 15% DKK, 10% SEK, 5% NOK.
- **Scenario distribution:**
  - Legitimate baseline: 95%
  - Flagged (total 5%):
    - 2% APP scam
    - 1.5% Mule network
    - 1% Sanction hit
    - 0.5% Velocity abuse
- **Fields:** align with internal event schema draft (payer/payee, amount, currency, scenario metadata, agent-ready flags).
- **Storage layout:**
  - `datasets/generated/streams/demo-v1.jsonl` (full stream)
  - `datasets/generated/summaries/demo-v1.csv` (aggregated counts by scenario + hour)
- **Quality gates:**
  - Deterministic seed for reproducibility (default 42).
  - Validation script to ensure counts per scenario ±0.1%. (TODO once repo scaffolding is live.)
