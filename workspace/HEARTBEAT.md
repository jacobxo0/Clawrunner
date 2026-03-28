# HEARTBEAT.md

# Tasks nedenfor køres af agenten ved hvert heartbeat-kald.

## Tasks

### Self-ping (kør ved hvert heartbeat)
Send en kort testbesked til Telegram chat ID 8572521981 og verificer at gateway er i live.
Hvis sendMessage API-kaldet fejler med timeout eller netværksfejl, log fejlen til workspace/memory/ og
rapporter straks til brugeren: "⚠️ Heartbeat fejl: Telegram API utilgængeligt — gateway muligvis nede"

### Groq API-status
Kald Groq API med en minimal prompt ("ping") og verificer at du får et svar inden 5 sekunder.
Hvis fejl (429, 401, timeout): rapporter til chat ID 8572521981:
"⚠️ Groq API fejl: [fejlkode] — skift til Ollama fallback hvis muligt"
