# Synthetic instant-payment stream generator

This module creates labelled instant-payment transactions aligned with the internal event schema draft.

## Scenarios covered
- `legit` – clean retail payment with normal velocity.
- `app_scam` – authorized push payment scam indicator (mismatched merchant category, sudden high value).
- `mule_network` – payer or payee linked to multiple counterparties within 24h.
- `sanction_hit` – counterparty IBAN/BIC matches synthetic sanctions list entry.
- `velocity_abuse` – burst of transactions from single IBAN above threshold.

## Outputs
- JSON Lines (`.jsonl`) with `event` objects, default 10_000 rows.
- Optional CSV summary for BI tooling.

## Usage
```bash
python synthetic_stream_generator.py --rows 50000 --seed 42 --out data/streams/demo.jsonl --scenarios legit app_scam mule_network sanction_hit velocity_abuse
```

The generator is deterministic when a seed is provided and inserts scenario-level metadata for downstream evaluation.
