# Investor memo outline (2 pages, v1.1)

1. **Executive summary**
   - One-paragraph narrative covering regulation trigger (EU IPR + UK PSR) + quantified pain (€1.2B APP fraud reimbursements, €2.8k avg reimbursement per case).
   - Funding ask: €3.5M seed (range €3–4M) for 24-month runway, milestones: ingest + scoring GA, 2 design partners live, compliance certification underway.
   - Include KPI commitments: <150ms decision latency, >90% fraud recall on synthetic set, 70% automated SAR drafting.
2. **Problem**
   - Detail regulator mandates (instant execution + reimbursement) forcing PSPs to upgrade detection within 12–18 months.
   - Metrics to cite: % EU PSPs lacking ISO 20022-native stack (~60%), manual investigation cost (avg €120 per alert), shortage of MLRO talent (source: EBA 2025 report).
   - Highlight enforcement specifics: EU IPR Article 5 deadlines (receive instant payments ≤9 months post-entry, send ≤18 months) + UK PSR mandatory reimbursement Q1 2025 causing 2× case volume.
   - Customer pain quotes TBD (need MLRO interviews) — flag as placeholder with note to capture testimonies from Tuum/Enfuce contacts.
3. **Solution**
   - Describe modular architecture, emphasize scoring mesh + agentic case bot + replay twin; include table of build status vs. roadmap phases.
   - Provide evidence requirements: synthetic dataset coverage (10 fraud scenarios), audit log schema, governance controls.
   - Add subsection on compliance automation pack (regulator-ready SAR drafts, replay exports) to reinforce defensibility vs. legacy vendors.
4. **Market & customers**
   - Segment table with counts per region (Nordics, DACH, Benelux, UK/Ireland) using ECB PSP register; annotate with compliance budgets (mid-tier banks €0.9–1.4M/yr on fraud ops).
   - Identify 3 target design partners (e.g., EMIs with SCT Inst exposure) with decision-maker roles (Head of Compliance, MLRO) and current contact status — draft list: Enfuce (FI, contact: MLRO pending), Banking Circle (LU/DK, contact: Head of Compliance via Copenhagen Fintech), ClearBank (UK, contact: PSD2 compliance lead).
   - Include readiness scorecard (data access, sandbox availability, regulator ties) so we can show Northzone/EQT we can activate pilots fast.
5. **Business model**
   - Pricing mechanics: base platform €25k/month for up to 10M tx, +€0.001 per extra tx, compliance pack add-ons €5–8k/month, managed detection €120/hr equivalent but value-priced as % of avoided headcount.
   - Include gross margin model (infra costs vs. human-in-the-loop) and path to 80% with automation.
   - Add worked example: 12M tx/month EMI → €27k base + €3k overage + €6k PSR pack + €8k managed automation = €44k MRR, 74% GM after €11.4k infra/support cost.
6. **Go-to-market**
   - Detail pilot plan: Q3 sandbox engagements (2), Q4 certification-backed pilots (2), conversion to ARR by Q1 2027.
   - Partnership motion: Copenhagen Fintech, Euro Banking Association, regulator sandboxes (DK FSA, Bank of Finland) — list application windows + requirements.
   - Metrics to report: sales cycle (<6 months), # of compliance workshops hosted, pipeline coverage (3× target ARR).
   - Add channel attribution plan (regulator briefings vs. partner webinars vs. direct MLRO network) to justify GTM spend.
7. **Team & execution plan**
   - Founder bio + relevant exits; highlight access to Ignis automation infrastructure.
   - Hiring plan table (role, timing, cost) for Head of Risk, Lead Engineer, Compliance Lead, Partner Success — add named candidates/in-progress convos where possible (e.g., ex-Nets MLRO, Tuum compliance architect).
   - Risk section: data access, certification delays, dependency on bank sandboxes — include mitigation steps (synthetic data, regulatory advisors, modular certification path).
8. **Financials & capital use**
   - Budget split reaffirmed (45/25/20/10) with euro figures (€1.6M / €0.9M / €0.7M / €0.3M).
   - Include cash runway scenarios (base vs. downside) and trigger metrics for Series A (ARR ≥ €4M, churn <5%, compliance certifications completed).
   - Add table of data required: infra cost quotes (GCP vs. Azure), certification fees (ISO/PCI), hiring benchmarks (market salary bands).
   - Insert "capital efficiency" view showing ARR per employee + burn multiple targets to satisfy Seedcamp/byFounders diligence templates.

**Appendices to compile:** regulation cheat sheet, data room checklist, KPI glossary, reference letters (once design partners engaged).
