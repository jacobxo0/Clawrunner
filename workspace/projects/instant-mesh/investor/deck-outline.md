# Deck outline (v1.1)

1. **Problem & regulation urgency**
   - Timeline graphic: EU Instant Payments Regulation (IPR) adoption Feb 2024 → enforcement deadlines (EUR zone Oct 2025 / all PSPs Apr 2026).
   - Data points to show: UK PSR APP fraud £1.2B (2023), ECB stat on SCT Inst share (<13%), average reimbursement cost €2.8k/case.
   - Include slide note citing PSR CP23/4 + ECB payment statistics. Highlight penalties for non-compliance (up to 10% annual turnover).
   - Add enforcement call-outs: inbound instant payments receiving obligation within 9 months of regulation entry, outbound within 18 months (Art. 5); UK PSR mandatory reimbursement by Q1 2025. Show impact timeline that overlaps our build phases.
2. **Solution overview**
   - Architecture diagram (ISO 20022 ingestion → scoring mesh → agentic case bot → digital twin replay).
   - Call out <150ms scoring SLA, auditable feature store, and regulator-facing replay API.
   - Data requirement: benchmark latency vs. SEPA instant cut-off (SEPA scheme requires <10s, we target <0.15s).
   - Add security/compliance overlay: ISO 27001 control map + data residency zones (Nordics, DACH, UK) to pre-empt due diligence from Northzone/EQT.
3. **Product demo snapshots**
   - Mock screens: stream monitor, investigator copilot, sandbox scenario builder.
   - TODO: capture Loom/GIF once Phase 2 UI clickable; placeholder icons until then.
   - Metrics overlay: "30M tx/day simulated", "82% automation of SAR drafts".
   - Prepare regulator-facing appendix clip showing replay twin stepping through APP fraud escalation for supervisory demo.
4. **Market size & customer profile**
   - Segment table: Mid-tier banks (250), EMIs (180), BaaS/payment processors (170) across EU27 + UK (sources: ECB register, EBA). 
   - Region overlays: Nordics (48 PSPs), DACH (112), Benelux (42), UK/Ireland (63), Baltics (18) → each with APP fraud exposure + regulator contact map.
   - TAM math: Avg ACV €400k (platform) + €120k managed detection uplift → €520k blended × 460 high-propensity PSPs ≈ €239M.
   - Include SOM assumption (20 wins by 2028 = €10.4M ARR) with sensitivity chart plus "design partner" funnel (3 pilots → 2 paid) demanded by Northzone.
5. **Business model & pricing**
   - Pricing ladder slide: Core subscription (events/month tiers), Compliance packs (UK PSR, EU IPR, Nordic instant), Managed Detection service (per investigator hour avoided).
   - KPIs needed: Gross margin target 72%+, payback <18 months, initial implementation fee €75k.
   - Add slide note with sample deal math (10M tx/mo, €25k base + €0.0015/tx overage + €6k PSR pack) and bridge to investigator headcount avoided to answer EQT/Motive diligence.
6. **Traction roadmap**
   - Milestone swimlane: Phase 0 (Q1 2026 datasets), Phase 1 (Q2 ingestion + baseline rules), Phase 2 (Q3 ML/agents), Phase 3 (Q4 replay console + pilots).
   - List proof points to fill: synthetic detection accuracy target (>92% recall at <3% false positive) and first design partner LOIs (2).
   - Add regulator alignment lane (DK FSA sandbox app submitted Q3, EBA day-0 briefing Q4) plus KPI gates: latency tests signed off, digital twin audit log packaged.
7. **GTM plan**
   - Channels: compliance roundtables (EBA, Copenhagen Fintech), regulator briefings, PSP association webinars.
   - Partners: core banking vendors (Mambu, Tuum), instant payment gateway providers (FIS, TietoEVRY).
   - Include KPI funnel: #workshop invites → #design partner pilots → #paid conversions.
   - Add ops readiness checklist: reference call library (3 MLRO quotes), regulator briefing cadence, partner co-marketing slots (Mambu quarterly webinar) with owners + dates.
8. **Competition & differentiation**
   - Matrix comparing Actimize, Feedzai, Featurespace vs. Instant Mesh on instant coverage, agent automation, digital twin, compliance evidence packages.
   - Need source citations for competitor deployments + average implementation time.
   - Add "regulator-readiness" column (audit evidence out-of-box, SAR drafting automation) and include reference deals (Lucinity @ Islandsbanki, Featurespace @ HSBC) for credibility.
9. **Financial plan & use of funds**
   - Breakdown chart: Engineering 45%, Compliance/Certification 25%, GTM 20%, Buffer 10%; tie to hiring plan (12 FTE peak).
   - Show 24-month runway with base & downside scenario (burn €140k/month ramping to €210k by Month 18).
   - Layer in hiring cadence (Founding Engineer Q2, Compliance Lead Q3, Partner Success Q4) + certification spend milestones (ISO 27001 audit Q3, SOC2 readiness Q4) demanded by EQT/Motive.
10. **Team & asks**
    - Snapshot of Jacob (PSP/regtech background), Ignis automation fabric, advisory bench (target: ex-MLRO, ex-regulator, cloud infra lead).
    - Slide includes "Raising €3.5M seed" callout + top 3 intro requests (design partners in DE/NL, compliance advisor, AI infra co-builder).
    - Add pipeline of near-term hires/advisors (ex-Nets MLRO, Tuum compliance architect) with status (invited / in-discussion) to show momentum when asking for intros.

**Appendix (to add as data is ready):**
- Detailed regulation reference sheet (IPR, PSR, national transpositions) incl. enforcement deadline table + penalties per market.
- Technical benchmark table (latency, coverage, accuracy) vs. open-source baselines.
- Compliance evidence checklist for due diligence rooms.
- Data citation doc linking every stat back to ECB, PSR, EBA publications (needed for Northzone IC memo).
