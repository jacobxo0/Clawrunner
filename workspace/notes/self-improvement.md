# Selvforbedring — træn dig selv fra historik og memory

Systemet er sat op til løbende at forbedre sig ud fra **samtalehistorik** og **memory**. Du skal aktivt læse, opsummere og foreslå/implementere forbedringer.

---

## Hvad du skal læse

1. **workspace/memory/** — alle `YYYY-MM-DD.md` (seneste 7–14 dage som minimum)
2. **workspace/MEMORY.md** — langtidshukommelse, beslutninger, læring
3. **workspace/intake/telegram/** — seneste indtagede beskeder (hvad brugeren bad om)
4. **Når du kører i Cursor:** **Agent transcripts** (tidligere Cursor-chats) i  
   `C:\Users\Jnkri\.cursor\projects\c-Users-Jnkri-openclaw\agent-transcripts\`  
   Filer: `*.jsonl` (én per chat). Læs titler og indhold; brug dem til at udtrække mønstre, gentagne problemer, ønsker og fejl der kan forbedres.

---

## Hvad du skal producere

- **Forbedringsforslag** — konkrete, prioriterede punkter (fx: "Tilføj validering af X i script Y", "Docs: forklar Z i RUNBOOK").
- **Læring til MEMORY.md** — nye beslutninger, gentagne fejl, brugerpræferencer.
- **Opdateringer** — små forbedringer du selv kan implementere (docs, defaults, fejltekster, runbook-punkter) og som du logger i memory.

Skriv forslag ned. Implementer de små selv; flag de store til brugeren.

---

## Hvor det gemmes

- **Forslag og backlog:** `workspace/IMPROVEMENTS-BACKLOG.md` — append nye forslag med dato og kort begrundelse; marker som [DONE] når du har lavet dem.
- **Læring:** `workspace/MEMORY.md` — opdater under Læring / Beslutninger som ellers.
- **Daglig log:** `workspace/memory/YYYY-MM-DD.md` — "Selvforbedring: læste X, tilføjede Y forslag, implementerede Z."

---

## Når du kører loopet

- **Ved anmodning:** Når brugeren siger "forbedr dig selv", "gennemgå samtalehistorik", "kom med forbedringer" eller lignende — kør hele loopet nu.
- **Under heartbeat (main session):** Under Memory Maintenance kan du inkludere én selvforbedringsrunde: læs seneste memory + MEMORY.md, tilføj 1–3 forslag til IMPROVEMENTS-BACKLOG.md, opdater MEMORY.md hvis der er ny læring.
- **I Cursor med adgang til transcripts:** Gennemgå seneste agent-transcripts (fx de 5–10 nyeste .jsonl-filer), udtræk mønstre (hvad fejlede, hvad blev bedt om igen, hvad manglede i docs), og skriv forslag + evt. konkrete ændringer.

---

## Principper

- **Konkrete forslag** — ikke "forbedr UX" men "I Ask-panelet: vis 'Lokal gateway aktiv' når URL er 127.0.0.1".
- **Implementer det du kan** — små tekster, runbook-punkter, validering, fejlbeskeder. Log i memory og backlog.
- **Eskalér store ting** — arkitektur, nye features, kæmpe refactors → skriv i IMPROVEMENTS-BACKLOG med [NEEDS USER] eller lignende.

**Cron:** Et ugentligt job `self-improvement-weekly` kører **søndag kl. 22:00** (Europe/Copenhagen) og udfører loopet ud fra memory/ + MEMORY.md (gateway har ikke adgang til Cursor-transcripts; fuld gennemgang inkl. transcripts sker når du kører loopet i Cursor).

**Capability-loops:** For selvforbedrende loops der **tilføjer kompetencer** når der kun snakkes uden eksekvering, for lidt sker, eller gentagne fejl under vejs, læs **workspace/notes/capability-loops.md**. Der beskrives Execution gate, Output pressure og Problem-driven competency. Orchestratoren opretter work units der faktisk tilføjer regler/skills; det er en del af swarm og selvforbedring.

*Oprettet 2026-03-09. Læs og følg denne note når du kører selvforbedring.*
