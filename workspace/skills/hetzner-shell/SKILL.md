# hetzner-shell

Kør kommandoer på Hetzner-serveren (178.104.83.125) via HTTP runner.

## Brug

```
hetzner-shell run <kommando>
```

## Eksempler

```
hetzner-shell run "docker ps"
hetzner-shell run "ollama list"
hetzner-shell run "df -h"
hetzner-shell run "systemctl status ollama"
hetzner-shell run "cd /opt/wallet-autopilot && npm start"
```

## Implementation

```js
const res = await fetch(process.env.HETZNER_RUNNER_URL + '/run', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-token': process.env.HETZNER_RUNNER_TOKEN
  },
  body: JSON.stringify({ cmd: command })
});
const { stdout, stderr, error } = await res.json();
```

## Hvad den kan

- Deploye projekter på serveren
- Starte/stoppe services
- Tjekke logs
- Køre scripts
- Installere pakker
- Alt hvad root kan på serveren

## Env vars krævet

- `HETZNER_RUNNER_URL` — http://178.104.83.125:9000
- `HETZNER_RUNNER_TOKEN` — secret token
