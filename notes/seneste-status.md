# Seneste status (agent-opdatering)

**Dato:** 2026-02-28

## Instant Mesh
- ✅ Datasæt-plan færdig: pacs.008-eksampler og syntetisk generator under `projects/instant-mesh/datasets/` (logget i build-log.md).
- ✅ CORE-F + prompt-hack framework dokumenteret i `projects/instant-mesh/notes/agent-system.md` (inkl. templates).
- 🚧 Monorepo-skeleton (backend/agents/ui/infra) + README + justfile + devcontainer under opbygning. Ændringer kommer ind i projektmappen snart.

**Blokering:** Ingen – GO givet.

## Wallet / crypto-arb
- Backend-venv virker (Cursor-run).
- 🚧 Reorganisering: wallet-log + monitor-skeleton. Første wallet-monitor (gas/spread polling, logformat, PnL-tracking) under udvikling; passer til UI og autosummaries. Første kode efter UI-squelette.

## Dashboard & CHECKLIST
- CHECKLIST.md i roden med CORE-F checkboxes – opdateres efter hver agent-run.
- 🚧 Dashboard skeleton (responsiv web, Vite + Tailwind) under opbygning; data-feed fra statusfiler; kanban + metrics. Kode uploades når data-binding er klar.

---

**Næste status:** Når Instant Mesh repo-skeleton er lagt + første wallet-monitor script findes i `projects/nft-arbitrage/`.
