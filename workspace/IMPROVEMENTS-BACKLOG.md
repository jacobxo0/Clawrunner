# IMPROVEMENTS-BACKLOG — forslag fra selvforbedring

Forslag fra gennemgang af memory, MEMORY.md og (når tilgængeligt) samtalehistorik. Append nye med dato. Marker som `[DONE]` når implementeret.

---

## Format per forslag

- **YYYY-MM-DD:** Kort beskrivelse. (Kilde: memory / transcripts / MEMORY.) [DONE] eller [PENDING] / [NEEDS USER]

---

## Eksempler (kan slettes når der er rigtige forslag)

- **2026-03-09:** RUNBOOK: tilføj "Hurtig helbredstjek" med netstat + validate:ollama + verify:dashboard. (Kilde: repair-session.) [DONE]
- **2026-03-09:** Dashboard: dev-default til lokal gateway (127.0.0.1:18789) + rigtig gateway-status ping. (Kilde: UI-aktivitet.) [DONE]

---

*(Nye forslag tilføjes herunder.)*

---

- **2026-03-08:** Telegram webhook var tom (getWebhookInfo url: ""). Sæt webhook til Railway eller ngrok og verificer at beskeder når gateway og at intake skrives. Se workspace/notes/DEBUG-TELEGRAM-NU.md. [PENDING]
