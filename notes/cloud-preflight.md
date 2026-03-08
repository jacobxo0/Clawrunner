# Cloud pre-flight — tjek før du starter

Gennemgå dette før du følger [cloud-deployment-runbook.md](c:\Users\Jnkri\.openclaw\notes\cloud-deployment-runbook.md).

---

## Du har

- [ ] **VPS** med Ubuntu 22.04 (fx Hetzner CX). IP-adresse: _______________
- [ ] **SSH-adgang:** du kan køre `ssh bruger@VPS_IP` fra din PC (nøgle eller password)
- [ ] **Brugernavn** på VPS (oftest `ubuntu`): _______________
- [ ] **OpenClaw** kører lokalt på din PC (openclaw.json, workspace, cron/jobs.json findes under `C:\Users\Jnkri\.openclaw`)

---

## Du har noteret

- [ ] **Gateway token** (fra openclaw.json → gateway.auth.token) — skal ind i VPS .env som OPENCLAW_GATEWAY_TOKEN
- [ ] **Brave API key** (fra openclaw.json → tools.web.search.apiKey) — skal ind i VPS .env som BRAVE_API_KEY

---

## Valgfrit

- [ ] **Tailscale** på PC (så du senere kan forbinde uden SSH-tunnel)
- [ ] **WSL eller Git Bash** med rsync (hurtigere workspace-upload end scp)

---

## Næste skridt

1. Åbn [notes/cloud-deployment-runbook.md](c:\Users\Jnkri\.openclaw\notes\cloud-deployment-runbook.md).
2. Start med **Del A** på VPS (Node, OpenClaw, mapper).
3. Brug **scripts/upload-to-vps.ps1** fra Windows (eller scp-kommandoerne i runbook Del B).
