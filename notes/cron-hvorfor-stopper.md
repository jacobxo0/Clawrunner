# Hvorfor cron jobs stopper — svar til Telegram/brugeren

Brug denne fil når brugeren spørger "hvorfor er cron stoppet", "hvorfor kører cron ikke", "cron jobs er stoppet" osv.

---

## Kort svar til brugeren

**Cron jobs kører kun når OpenClaw-gatewayen kører.** Hvis cron "er stoppet", er det næsten altid fordi:

1. **Gatewayen kører ikke** — processen er lukket, PC'en er blevet genstartet, eller gatewayen blev aldrig startet. Cron-motoren sidder i gatewayen; uden gateway sker der ingen planlagte kørsel.
2. **PC'en sover eller er lukket** — gatewayen kører kun mens den proces kører på den maskine.

**Løsning:** Start gatewayen igen og lad den køre (evt. i baggrunden):

```powershell
cd c:\Users\Jnkri\.openclaw
.\scripts\start-gateway.ps1
```

Efter start læser gatewayen `cron/jobs.json` og kører jobs på de planlagte tidspunkter (instant-mesh-build 08:00, instant-mesh-investor man/ons 10:00, instant-mesh-status 20:00).

---

## Tjek selv (til agenten)

- **Er gatewayen oppe?** `netstat -an | findstr 18789` — hvis port 18789 ikke lytter, kører gatewayen ikke.
- **Er jobs stadig aktive?** I `cron/jobs.json` har hvert job `enabled: true` og `state.lastStatus`. Hvis `lastStatus` er `ok` og `enabled` er true, er jobbet ikke "slået fra" — det venter bare på at gatewayen kører, så næste `nextRunAtMs` kan blive udløst.

---

*Oprettet så Telegram-botten kan svare præcist når brugeren spørger hvorfor cron er stoppet.*
