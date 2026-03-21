# Capability-loops — vilde selvforbedrende loops

Orchestratoren skal ikke kun køre swarm-cykler; den skal **oprette loops der gør systemet klogere** ved at tilføje kompetencer når problemer opstår, der sker for lidt, eller der kun snakkes uden eksekvering.

---

## Tre typer capability-loops

### 1. Execution gate (snak uden eksekvering)

**Trigger:** Mange beskeder/turns uden verificerbare artefakter — ingen filændringer, ingen kørte kommandoer, kun diskussion eller planlægning.

**Handling:** Orchestratoren opretter en **work unit** med formål: *Tilføj kompetence der kræver verificerbar output.*

- **Executor:** Tilføj eller opdater en regel/skill der siger: efter planlægning eller diskussion skal næste skridt være enten (a) en konkret filændring, (b) en kørt kommando/script, eller (c) en eksplicit BLOCKED med årsag. Fx i `.cursor/rules/` eller i swarm-kernel reference under "Execution gate".
- **QC:** Tjek at reglen er konkret og at den næste turn kan måles (fil/kommando/blocked).
- **Release:** Regel/skill er på plads; næste swarm-cyklus følger den.

**Resultat:** Modellen/agenten bliver "tvunget" til at levere eksekvering, ikke bare snak.

---

### 2. Output pressure (for lidt sker)

**Trigger:** Cykler hvor ingen work units bliver DONE, eller meget få ændringer over flere runs (fx heartbeat eller swarm-cycle uden konkrete deliverables).

**Handling:** Orchestratoren opretter en **work unit**: *Tilføj kompetence der øger eksekveringspres.*

- **Executor:** Tilføj checkpoint eller reminder der aktivt spørger: "Har denne cyklus produceret mindst ét verificerbart deliverable (fil, deploy, test run)?" — fx i HEARTBEAT.md eller i swarm-cycle prompten. Eller tilføj til IMPROVEMENTS-BACKLOG en konkret "execution checkpoint" opgave og marker den som påkrævet før "ingen mere arbejde".
- **QC:** Tjek at checkpointet er læsbart og at det vil blive evalueret i den relevante kontekst.
- **Release:** Næste kørsel inkluderer pres for mindst ét deliverable per cyklus.

**Resultat:** Systemet stiller krav til sig selv om at noget sker, ikke bare at der planlægges.

---

### 3. Problem-driven competency (problemer under vejs)

**Trigger:** Gentagen QC-fejl, samme fejltype flere gange, gentagen routing-fejl, eller capability escalation fra swarm-kernel (se reference.md § Capability Escalation).

**Handling:** Orchestratoren opretter en **work unit**: *Tilføj kompetence der forhindrer eller reducerer denne fejl.*

- **Executor:** Opret eller opdater (a) en **skill** (fx under `.cursor/skills/` eller workspace) der beskriver hvordan man undgår fejlen og hvilke skridt der altid skal tages, eller (b) en **.cursor/rule** (eller punkt i reference.md / AGENTS.md) der eksplicit forbød den påviste anti-pattern. Dokumentér i IMPROVEMENTS-BACKLOG som [DONE] med kort beskrivelse.
- **QC:** Tjek at skill/regel er specifik og at den adresserer den observerede fejl.
- **Release:** Ny kompetence er tilgængelig for fremtidige cykler; evt. tilføj til MEMORY.md som "Tilføjet kompetence: [kort]".

**Resultat:** Hver gang et mønster fejl opstår, tilføjes en evne så det ikke gentages.

---

## Hvordan orchestratoren bruger loopsene

1. **Under swarm-cyklus:** Efter hver cyklus (eller efter N turns) vurdér:
   - Var der kun snak/plan uden fil/kommando? → Opret work unit for **Execution gate**.
   - Blev der lavet for lidt (ingen DONE units)? → Opret work unit for **Output pressure**.
   - Opstod samme fejl/QC-fejl igen? → Opret work unit for **Problem-driven competency**.

2. **Under selvforbedring:** Når du læser memory/ og agent-transcripts, brug mønstre (fx "gentagen diskussion uden eksekvering") som trigger og opret tilsvarende forslag i IMPROVEMENTS-BACKLOG med label [CAPABILITY] og beskrivelsen fra ovenstående.

3. **Capability-cyklus (cron/heartbeat):** Et job kan køre fx ugentligt eller efter swarm-cycle: "Læs workspace/notes/capability-loops.md. Tjek seneste memory og swarm-resultater for (1) snak uden eksekvering, (2) for lidt output, (3) gentagne fejl. For hvert fund: opret work unit eller tilføj [CAPABILITY]-forslag til IMPROVEMENTS-BACKLOG og udfør det næste gang swarm kører."

---

## Hvor det gemmes

- **Nye regler/skills:** `.cursor/rules/`, `.cursor/skills/`, eller `workspace/notes/` + reference i AGENTS.md / swarm-kernel reference.
- **Backlog:** `workspace/IMPROVEMENTS-BACKLOG.md` — marker [CAPABILITY] på forslag der kommer fra disse loops.
- **Læring:** `workspace/MEMORY.md` — "Tilføjet kompetence: [hvad] pga. [trigger]."

---

## Principper

- **Konkrete kompetencer** — ikke "vær bedre til X" men "efter planlægning: næste turn skal indeholde fil-ændring, kørt kommando, eller BLOCKED."
- **Orchestratoren opretter work units** — den uddelegerer ikke til brugeren at "tilføj en regel"; den lægger en work unit så Executor/QC/Release faktisk tilføjer reglen.
- **Evidensbaseret** — kun tilføj kompetence når mønsteret er observeret (gentagen fejl, manglende output, kun snak). Én enkelt fejl er ikke nok medmindre den er strukturel.

*Oprettet 2026-03-09. Læs og følg denne note når du kører capability-loops eller capability-cyklus.*
