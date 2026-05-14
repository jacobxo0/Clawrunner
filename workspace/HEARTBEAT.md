tasks:

- name: memory-maintenance
  interval: 2h
  prompt: "Read workspace/memory/ (today + yesterday). Distill anything worth keeping into MEMORY.md. Remove stale entries. If nothing new, reply HEARTBEAT_OK."

- name: improvements-check
  interval: 6h
  prompt: "Read workspace/IMPROVEMENTS-BACKLOG.md. Pick one [PENDING] item small enough to implement now. Implement it, mark [DONE] with today's date. If nothing small enough, reply HEARTBEAT_OK."

- name: self-check
  interval: 4h
  prompt: "Check MEMORY.md for any ACTION REQUIRED or BLOCKED items. If found, surface them briefly. Otherwise reply HEARTBEAT_OK."

# Tung arbejde kører som isolerede cron jobs i cron/jobs.json — ikke her.
# Hold denne fil lille for at undgå token-spild.
