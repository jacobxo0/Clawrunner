# Research-plan: Commodity Arbitrage (metaller / ædelstene)

**Formål:** Strukturere research så den ender i en Feasibility Gate → GO/NO-GO med kilder.  
**Rapport:** `reports/2026-03-01-commodity-arbitrage.md`

---

## Scope (hvad vi undersøger)

| Dimension | Indhold |
|-----------|---------|
| **Produkter** | Metaller (guld, sølv, PGM), ædelstene (diamanter, farvede sten, perler) — pr. beslutning |
| **Markeder** | OTC (London, Dubai, Schweiz), refiners/LBMA, auktionshuse, andre relevante kanaler |
| **Lovkrav** | KYC/AML, eksport/import, told, moms, licenser, capital requirements |

---

## Feasibility Gate — de fire blokke

1. **Hvor kommer spreadet fra?**  
   Typiske arbitrage-kanaler, prisdifferencer mellem markeder/kvaliteter. Krav: konkrete kilder til spreads (når Brave API er sat).

2. **Forsendelse og sikkerhed**  
   Logistik, transport, forsikring, custody. Krav: kilder til leverandører og typiske fees/risici.

3. **Licenser og capital**  
   Hvilke tilladelser og minimumskapital kræves pr. marked/kanal? Krav: kilder til aktuelle krav.

4. **Risikovurdering**  
   Scams, logistik-problemer, reguleringsændringer. Krav: kort risikovurdering med henvisninger.

---

## Baseline vs. live-data

- **Baseline:** Eksisterende viden (pre-2024, noter) — udfyldes i rapporten uden web search.
- **Live-data:** Friske kilder (regulering, spreads, leverandører) — kræver **Brave Search API** i OpenClaw. Når `openclaw configure --section web` er kørt (eller `BRAVE_API_KEY` sat), kan agenten/du køre web-forespørgsler og udfylde de resterende sektioner.

---

## Næste skridt

1. Uddyb baseline i `reports/2026-03-01-commodity-arbitrage.md` (Sektion 1–3).
2. Konfigurér Brave API (se `notes/brave-search-api.md` i OpenClaw-roden).
3. Kør web research og udfyld Sektion 2.1–2.4, 4 og 5 med kilder.
4. Afslut med GO/NO-GO (Sektion 6).
