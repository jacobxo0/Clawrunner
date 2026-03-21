# OpenClaw Agent Operating Model

Overordnet ramme for alle agenter (Instant Mesh, Wallet, Reklame-generator). Hver agent logger hvilken fase den er i og bruger prompt-hacks fra kataloget.

---

## 1. CORE-F — standardcyklus

| Fase | Beskrivelse |
|------|-------------|
| **C — Comprehend** | Indlæs data, brief, kontekst. |
| **O — Orchestrate** | Planlæg execution (ToT/ReAct). |
| **R — Respond** | Kør scripts, API-kald, filændringer. |
| **E — Evaluate** | Evaluer output: kvalitet, PnL, fejl. |
| **F — Fine-tune** | Juster parametre, feedback til næste run. |

Log altid fase + kort resultat i projektets logfil. Blocker: marker med `ACTION REQUIRED:`.

---

## 2. Prompt Strategy Pack (udvalgte hacks)

| Hack | Brug |
|------|------|
| Role assignment | "Du er X med ekspertise i Y." |
| Output format | "Svær i max 3 bullet points / JSON." |
| Two-pass | Først grov, derefter præciser. |
| Blind spot | "Hvad har du overset?" |
| Checklist | Afkrydsningsliste før aflevering. |
| Teach-back | "Forklar som om jeg ikke kender domænet." |
| Precision | Præcise tal, datoer, kilder. |
| Error spotting | List fejl og mitigering. |
| Recursive exploration | "Hvis A, så B; hvis B fejler, så C." |
| Constraint injection | Max N ord, tone: X. |

Udvid med flere i `workspace/skills/prompts/` efter behov.

---

## 3. Feedback og learning (F)

- E-fase: kort selvbedømmelse.
- Auto-finetune: log parametre + resultat; næste run kan foreslå justeringer.
- StatusWeaver/cron viser CORE-F-fase og ACTION REQUIRED.

---

## 4. Per-projekt specs

- **Instant Mesh:** `workspace/projects/instant-mesh/notes/agent-system.md` + `workspace/agents/instant-mesh/*.md`.
- **Wallet:** Agent-spec med C/O/R/E/F + prompt-profil.
- **Reklame-generator:** Brief → CORE-F + hacks (Role, Two-pass, Checklist).

---

## 5. Referencer

- Cron: `cron/CRON-SETUP.md`
- Runbook: `RUNBOOK.md`
- Checklist: `CHECKLIST.md`
