# Cloud Migration Plan (draft)

## Target
- Run OpenClaw + Ollama centrally in cloud (CPU-first, optional GPU as add-on).
- Local PCs act as thin clients.
- External HDD used for nightly backups.

## Fuld trin-for-trin guide
Se **`notes/setup-openclaw-paa-cloud.md`** (OpenClaw-roden) for detaljeret opsætning: VPS-valg, gateway bind, Telegram/cron på VPS, remote mode fra PC, Ollama, backup.

## Steps
1. Choose provider (Hetzner CX for CPU baseline, optional RunPod GPU burst).
2. Provision server (Ubuntu 22.04, hardened per Aaron guide).
3. Install base stack (OpenClaw, Ollama, git, monitoring).
4. Sync workspace from current Windows box (OneDrive/Git mirror).
5. Configure remote triggers so old PC still runs jobs until cutover.
6. Set up backup job to external HDD.
7. Move control UI to new PC.
