# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Miljø

- **Platform:** Railway, Linux (Debian bookworm-slim), Node 22
- **Workspace:** `/app/workspace`
- **Gateway URL:** `https://clawrunner-production.up.railway.app`
- **AI-CORE URL:** Se Railway Variable `AI_CORE_URL`

## Aktive Skills (bekræftet virker på Linux)

| Skill | Hvad den kan |
|-------|-------------|
| `clawhub` | Søg og installer skills fra registry |
| `memory-core` | Persistent hukommelse på tværs af sessioner |
| `file-transfer` | Læs/skriv filer i workspace |
| `ai-core` | Shell-kommandoer, HTTP-kald, run-historik via AI_CORE_URL |
| `blogwatcher` | RSS/Atom feed monitoring |
| `coding-agent` | Delegér kode-opgaver til ekstern coder |

## Blokerede Skills (kræver macOS — ignorer dem)

`apple-notes`, `apple-reminders`, `bear-notes`, `1password`, `blucli`, `bluebubbles`, `camsnap`

## Installed Skills (opdatér når du installerer nye)

| Skill | Fil | Kræver |
|-------|-----|--------|
| `tavily-search` | `workspace/skills/tavily-search/SKILL.md` | `TAVILY_API_KEY` |
| `jina-reader` | `workspace/skills/jina-reader/SKILL.md` | Ingen (gratis) |
| `fal-image` | `workspace/skills/fal-image/SKILL.md` | `FAL_API_KEY` |
| `ai-core` | `workspace/skills/ai-core/README.md` | `AI_CORE_URL` |

## Marketing Pipeline Agents

| Agent | Fil | Rolle |
|-------|-----|-------|
| `DISPATCHER` | `workspace/agents/DISPATCHER.md` | Intent-router, starter pipelines |
| `COPY_AGENT` | `workspace/agents/COPY_AGENT.md` | Tekst, narrative, tone |
| `VISUAL_AGENT` | `workspace/agents/VISUAL_AGENT.md` | Billedgenerering via fal.ai |
| `RESEARCH_AGENT` | `workspace/agents/RESEARCH_AGENT.md` | Markedsdata, konkurrenter |

## Skill Acquisition Workflow

```
1. clawhub search <hvad du mangler>
2. clawhub install <skill-name>
3. Test den
4. Tilføj til "Installed Skills" ovenfor
```

Add whatever helps you do your job. This is your cheat sheet.
