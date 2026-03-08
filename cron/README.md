# Cron — status

**jobs.json** indeholder nu **3 planlagte jobs** (instant-mesh-build, instant-mesh-investor, instant-mesh-status). Gatewayen læser filen ved opstart.

## Vigtigt

- **Genstart gatewayen** så den indlæser de nye jobs: stop den nuværende gateway-proces og start igen med `scripts\start-gateway.ps1` eller `gateway.cmd`.
- Efter genstart kører BuildConductor dagligt 08:00, InvestorScout man/ons 10:00, StatusWeaver dagligt 20:00 (CET).
- Tjek at jobs er loadet: `openclaw cron list` (mens gateway kører).

## Kør et job nu

Gatewayen bruger **UUID** som job-id (ikke navnet). Find id med `openclaw cron list`, kør derefter:

```powershell
openclaw cron run <uuid>
```

Eksempel (BuildConductor): `openclaw cron run 41436810-8e5b-4d75-ab5f-c57ee4088580`

## Tilføj/fjern jobs

- Via CLI: `openclaw cron add ...` (se CRON-SETUP.md).
- Manuelt: Stop gateway, rediger `jobs.json`, start gateway igen.
