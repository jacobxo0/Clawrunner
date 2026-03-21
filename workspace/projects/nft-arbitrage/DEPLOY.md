# NFT Arbitrage OS — VPS deployment (24/7)

Så systemet kører selv når din computer er slukket. Du logger ind på VPS'en, starter containeren, og lukker SSH — botten kører videre.

---

## 1. Vælg en VPS

- **Hetzner** (CX22): ~€4/md, 2 vCPU, 4 GB RAM — rigeligt
- **DigitalOcean** (Basic): $6/md
- **Contabo / OVH**: billige alternativer

Krav: **Ubuntu 22.04** (eller 24.04), public IP, 1 GB RAM minimum.

---

## 2. Forbered serveren (én gang)

SSH ind og kør:

```bash
# Opdater system
sudo apt update && sudo apt upgrade -y

# Docker
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Log ud og ind igen så "docker" uden sudo virker
```

---

## 3. Kopiér projektet til VPS

**Fra din Windows-maskine** (PowerShell, fra projektmappen):

```powershell
# Pak projektet (uden .env — den sætter du op manuelt på VPS)
scp -r "c:\Users\Jnkri\OneDrive\Skrivebord\NFT Arbitrage" bruger@DIN_VPS_IP:~/
```

Eller brug **Git** hvis du har repo:

```bash
# På VPS
git clone <dit-repo> ~/nft-arbitrage
cd ~/nft-arbitrage
```

---

## 4. Opret .env på VPS

På VPS:

```bash
cd ~/NFT\ Arbitrage   # eller ~/nft-arbitrage

# Kopiér din lokale .env (eller opret ny)
nano .env
```

Sæt **mindst** disse (samme værdier som lokalt):

- `DATABASE_URL=sqlite+aiosqlite:////app/data/nft_arbitrage.db`
- `ETH_RPC_URL=...` (helst Alchemy/Infura, ikke public)
- `ETH_PRIVATE_KEY=0x...`
- `OPENSEA_API_KEY=...`
- `REDIS_URL=redis://localhost:6379/0` eller udelad (så bruges in-memory cache)

Opret data-mappe så DB bliver gemt på disken:

```bash
mkdir -p data
```

---

## 5. Start botten (24/7)

```bash
cd ~/NFT\ Arbitrage
docker compose up -d
```

Tjek at den kører:

```bash
docker compose ps
docker compose logs -f app
```

Dashboard: **http://DIN_VPS_IP:8000**

Når du lukker SSH, kører containeren videre. Genstart ved reboot (medmindre du har slået Docker fra).

---

## 6. Nyttige kommandoer

| Kommando | Betydning |
|----------|-----------|
| `docker compose logs -f app` | Se live logs |
| `docker compose restart app` | Genstart app |
| `docker compose down` | Stop alt |
| `docker compose up -d --build` | Genbuild + start (efter kodeændring) |

---

## 7. "Steroider" — flere billige collections, mere volumen

Din logik: **flere billige collections = mindre hård konkurrence**. Det matcher hvad systemet allerede gør (billige floors, lavere konkurrence).

### A) Flere ultra-billige collections

I `config/settings.yaml` under `collections:` kan du tilføje flere med lav floor (&lt; 0.02 ETH). Find fx på [OpenSea](https://opensea.io) eller [NFTScan](https://nftscan.com) — søg på "floor price low". Eksempel (tjek selv slug/contract før brug):

```yaml
  - slug: "ethereums"
    name: "Ethereums"
    chain: "ethereum"
    contract: "0x..."
    royalty_bps: 500
    marketplace_fee_bps: 250
    active: true
```

Jo flere **aktive** billige collections, jo flere muligheder — især når wallet stadig er lille.

### B) Hurtigere scanning

I `config/settings.yaml` under `scheduling:`:

```yaml
scheduling:
  ingestion_interval_seconds: 6   # var 10 — hurtigere data
  opportunity_scan_seconds: 12    # var 20 — hurtigere scan
```

Og under hver strategi (fx `strategies.bid_spread`):

```yaml
  bid_spread:
    scan_interval_seconds: 15   # hurtigere bid_spread-scan
```

**Pas på**: for lav interval = flere API-kald, risiko for rate limit fra OpenSea. 6–10 s ingestion og 12–15 s scan er ofte et godt kompromis.

### C) Redis på VPS (valgfrit)

I `docker-compose.yml` kan du udkommentere Redis og `depends_on` + `REDIS_URL`. Så bruger appen Redis i stedet for in-memory cache — bedre ved genstart og lidt mindre load på OpenSea.

---

## 8. Sikkerhed (kort)

- **Firewall**: Åbn kun port 22 (SSH) og evt. 8000 (dashboard). Ellers: brug SSH tunnel i stedet for at åbne 8000 til hele verden.
- **.env**: Kommer ikke med i Docker-image; den læses fra host. Sørg for at mappen ikke er læsbar for andre (`chmod 700` på mappen eller brugeren).
- **Private key**: Kun på VPS'en i .env — brug en dedikeret wallet til botten, ikke din hovedwallet.

---

## Kort opsummering

1. Lej en lille VPS (Ubuntu).
2. Installer Docker, kopiér projektet, opret `.env` og `data/`.
3. Kør `docker compose up -d`.
4. Åbn **http://VPS_IP:8000** når du vil tjekke status.
5. Skru evt. op med flere billige collections og hurtigere scan-intervals ("steroider").

Så kører systemet 24/7, også når du ikke er ved computeren eller den er slukket.
