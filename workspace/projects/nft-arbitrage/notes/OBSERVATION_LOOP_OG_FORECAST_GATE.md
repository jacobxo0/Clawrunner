# Observation loop og forecast-gate

## Formål

1. **Konstant observation** — en loop-motor kører jævnligt og lagrer markedsstate (spread, bid depth, floor, volume) som **viden**. Så har systemet altid frisk kontekst og historik at reagere på før handler.
2. **Kun trade hvor vi kan forecast lige så godt som andre med succes** — før en handel gennemgår den en **forecast-gate**: i lignende situationer (samme strategi, collection, spread-interval), hvad var vores hit rate? Kun hvis hit rate ≥ benchmark (fx 55 %) og vi har nok datapunkter, godkendes handlen.

## Komponenter

### Observation loop (loop-motor)

- **Worker:** `src/workers/observation_loop_worker.py`
- **Tabel:** `market_observations` — én række per collection per observationstidspunkt med spread_pct, bid_depth, floor_eth, best_bid_eth, num_listings, num_bids, volume_24h_eth.
- **Scheduler:** Kører hver 45 s (konfigurerbart: `scheduling.observation_loop_seconds`).
- **Config:** `config/settings.yaml` → `observation_loop.enabled`, `observation_loop.max_collections_per_cycle`.

### Beslutningsviden (decision knowledge)

- **Tabel:** `decision_knowledge` — for hver beslutning vi tager (når vi overvejer at execute) gemmes kontekst: strategy, collection_id, spread_pct, bid_depth, roi_pct, fill_prob_predicted, buy_price_eth. Når vi har udfald (fyldt / ikke fyldt, PnL) opdateres outcome_filled og outcome_pnl.
- **Service:** `src/engine/knowledge_store.py` — `record_decision()` kaldes før execution, `record_outcome()` efter execution.

### Forecast-gate

- **Modul:** `src/engine/forecast_gate.py`
- **Logik:** For en given opportunity (strategy, collection, spread, bid_depth) spørger vi: i de seneste N dage, i lignende situationer (spread og bid_depth inden for tolerance), hvor mange gange fik vi en fyldt trade? Hit rate = filled / total. Hvis `hit_rate < min_benchmark_hit_rate` (fx 0,55) og vi har mindst `min_sample_size` datapunkter → **bloker** handlen.
- **Config:** `config/settings.yaml` → `forecast_gate`:
  - `min_benchmark_hit_rate`: 0,55
  - `min_sample_size`: 5
  - `allow_if_insufficient_data`: true (hvis vi ikke har nok historik, tillad handlen indtil vi har data)
  - `lookback_days`: 90
  - `spread_tolerance_pct`, `bid_depth_tolerance`: for at matche "lignende" situationer

## Flow

1. **Observation loop** kører kontinuerligt → skriver `market_observations`.
2. **Scan worker** finder opportunities → QC → **forecast gate**: `allowed(opp, collection_data)`. Hvis ikke allowed, logges det og vi **executer ikke** (opportunity gemmes stadig, kan sendes til manuel review).
3. Hvis forecast gate tillader: **record_decision(...)** → så **should_auto_execute_async** → **execute_opportunity** → **record_outcome(opportunity_id, filled, pnl)**.
4. Over tid bygges der mere og mere viden i `decision_knowledge`; forecast-gate bliver skarpere og tillader kun handler hvor vi historisk har forecastet mindst lige så godt som benchmark.

## Nye tabeller (migration)

Kør Alembic for at oprette tabellerne i eksisterende DB:

```bash
alembic upgrade head
```

Eller ved frisk install bruger `init_db()` alle modeller inkl. de nye, så tabeller oprettes automatisk.

## Kort sagt

- **Loop-motor** = konstant observation lagret som viden.
- **Forecast-gate** = kun trade når vi i lignende situationer har en hit rate der er mindst lige så god som den konfigurerede benchmark (succesfulde aktørers niveau).
