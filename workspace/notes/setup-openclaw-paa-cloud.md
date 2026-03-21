# OpenClaw kørende på cloud

Så gateway, Telegram og cron kan køre i skyen (VPS); lokale PC'er bruges som kontrol. Fuld version også i OpenClaw-roden: `notes/setup-openclaw-paa-cloud.md`.

---

## Mål

- **Gateway + Telegram + cron** kører på en VPS → Telegram svarer og cron kører 24/7 selv når PC'en er slukket.
- **Lokale PC'er** forbinder sig via Tailscale eller SSH-tunnel (remote mode).
- **Ollama** valgfrit på samme VPS eller separat. **Workspace** på VPS; backup til ekstern disk eller cloud.

---

## Kort svar til brugeren (Telegram / chat)

- **Ja, det kan køre på cloud.** Samme bot-token, samme cron-jobs; gatewayen kører bare på VPS i stedet for på PC. PC'er bruger remote mode (SSH-tunnel eller Tailscale) til at styre gatewayen.
- **Trin:** 1) Vælg VPS (fx Hetzner CX, Ubuntu 22.04). 2) Installér Node, OpenClaw; kopiér openclaw.json og workspace. 3) Start gateway på VPS (evt. systemd/screen). 4) På PC: SSH-tunnel eller Tailscale + remote URL/token. 5) Valgfrit: Ollama på VPS, backup-job.
- **Fuld guide:** `notes/setup-openclaw-paa-cloud.md` (OpenClaw-roden) og `workspace/notes/cloud-migration-plan.md`.

---

## Oversigt: hvad kører hvor

| Komponent   | Lokal (nu)        | Cloud (mål)              |
|-------------|-------------------|---------------------------|
| Gateway     | PC, port 18789    | VPS, port 18789           |
| Telegram-bot| Samme token       | Samme token; svarer fra skyen |
| Cron        | Kun når PC-gateway kører | Kører når gateway på VPS kører |
| Workspace   | Din PC            | VPS (synk/kopi)           |
