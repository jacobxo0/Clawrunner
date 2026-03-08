# Plan: Ollama på VPS — så Railway-gatewayen kan bruge den

Ollama kører på en VPS; gatewayen (Railway eller anden) peger på VPS’en via URL. Ingen Ollama lokalt på din PC.

---

## Mål

- **Ollama** kører på en VPS (Ubuntu), port 11434, med mindst ét tool-capable model.
- **Gateway** (fx på Railway) har i config en Ollama-provider med `baseUrl: "http://<VPS-IP>:11434"`, så agenter kan bruge Ollama-modeller.
- **Sikkerhed:** Port 11434 åben kun for gatewayens kilder (Railway IP-range, Tailscale eller VPN), ikke hele internettet – medmindre du bevidst eksponerer den.

---

## Fase 1: VPS klar

| # | Handling | Detaljer |
|---|----------|----------|
| 1.1 | Vælg og opret VPS | Ubuntu 22.04, fx Hetzner CX (8 GB RAM minimum for mindre modeller; llama3.3 70B kræver mere – overvej mindre model fx `llama3.2:3b` eller `qwen2.5-coder:7b`). |
| 1.2 | SSH-adgang | `ssh root@<VPS-IP>` eller `ssh ubuntu@<VPS-IP>` med nøgle. |
| 1.3 | Firewall | Åbn 22 (SSH), 11434 (Ollama). Begræns 11434 til Railway IP-range eller brug Tailscale så kun din gateway når Ollama. |

---

## Fase 2: Installér Ollama på VPS

**Én kommando på VPS** (efter SSH): kopiér scriptet op og kør det, eller kør kommandoerne nedenfor manuelt.

| # | Handling | Kommandoer / noter |
|---|----------|---------------------|
| 2.0 | **Script (anbefalet)** | På VPS: `curl -sSL <repo-raw>/scripts/install-ollama-vps.sh -o install-ollama-vps.sh && chmod +x install-ollama-vps.sh && sudo ./install-ollama-vps.sh`. Eller kopiér indholdet af `scripts/install-ollama-vps.sh` til VPS og kør `bash install-ollama-vps.sh`. |
| 2.1 | Installér Ollama (Linux) | `curl -fsSL https://ollama.com/install.sh | sh` |
| 2.2 | Start tjeneste | `sudo systemctl start ollama`, `sudo systemctl enable ollama`. |
| 2.3 | Tjek port | `curl http://127.0.0.1:11434/api/tags` eller `ollama list`. |
| 2.4 | Pull model | Fx `ollama pull llama3.2:3b` (lille) eller `ollama pull qwen2.5-coder:7b`. |
| 2.5 | Firewall | Scriptet åbner 22 og 11434 med ufw. Begræns 11434 til Railway-IP hvis du vil (se scriptets output). |

---

## Fase 3: Gateway peger på VPS-Ollama

Gatewayen (Railway eller anden) skal kende Ollama på VPS.

| # | Handling | Detaljer |
|---|----------|----------|
| 3.1 | VPS’ens adresse | Enten public IP (`http://<VPS-IP>:11434`) eller Tailscale-hostname (`http://<vps-tailscale-name>:11434`) hvis du bruger Tailscale. |
| 3.2 | Config på Railway | I Railway **Variables** tilføj **`OLLAMA_BASE_URL`** = `http://<VPS-IP>:11434` (uden `/v1`). Template `openclaw.railway.example.json` indeholder allerede Ollama-provider; start-scriptet inkluderer den kun når `OLLAMA_BASE_URL` er sat. |
| 3.3 | Eller lokal openclaw.json | Hvis du kører gateway lokalt: tilføj `models.providers.ollama` med `baseUrl: "http://<VPS-IP>:11434"`. Se [notes/ollama-setup.md](ollama-setup.md) "Hvis Ollama kører på en anden maskine". |
| 3.4 | OLLAMA_API_KEY | Valgfrit: sæt fx `OLLAMA_API_KEY=ollama-vps` i Railway Variables. |
| 3.5 | Redeploy | Efter du har sat `OLLAMA_BASE_URL` på Railway: redeploy. Kør `openclaw models list` – Ollama-modeller fra VPS’en bør optræde. Model `ollama/llama3.2:3b` (alias Ollama) er i template. |

---

## Fase 4: Sikkerhed (anbefalet)

- **Begræns adgang til 11434:** Brug firewall (ufw) så kun bestemte IP’er (fx Railway egress IP’er eller din Tailscale-net) kan forbinde. Eller kør Ollama bag Tailscale og brug Tailscale-hostname i `baseUrl`.
- **Ingen sensitive data i modeller:** Selv-hostede modeller logger typisk ikke til tredjepart; data forbliver på din VPS.

---

## Referencer

- **Ollama install (Linux):** [ollama.com](https://ollama.com) → Install.
- **OpenClaw + Ollama på anden maskine:** [notes/ollama-setup.md](ollama-setup.md).
- **Cloud/VPS generelt:** [notes/setup-openclaw-paa-cloud.md](setup-openclaw-paa-cloud.md), [notes/cloud-deployment-runbook.md](cloud-deployment-runbook.md).

---

## Lokal Ollama (PC) — slukket

Den lokale Ollama på din PC er stoppet (processer lukket). Hvis du har tilføjet `ollama/llama3.3` i `openclaw.json` og kun vil bruge VPS-Ollama fremover, kan du enten: (1) lade model-entry stå og sørge for at provider `baseUrl` peger på VPS, så samme model-id bruger VPS’en, eller (2) fjerne den lokale Ollama-model fra config indtil VPS-Ollama er sat op og tilføje provider + model igen med VPS-baseUrl.

*Oprettet 2026-03-07.*
