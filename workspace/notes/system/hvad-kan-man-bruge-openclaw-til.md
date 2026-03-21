# Hvad kan man egentlig bruge OpenClaw til?

Kort og ærligt.

---

## Det OpenClaw **er**

Et **lokal AI-assistent-platform**: en gateway der kører på din maskine, kobler dig til en AI med adgang til **din workspace** (filer, projekter), og kan køre ting **på plan** (cron) eller når du beder om det (chat / spawn).

---

## Hvad du **konkret** kan bruge det til

| Brug | Hvordan |
|------|--------|
| **Chat med en AI der kender din kode** | Du skriver i Telegram (eller anden kanal). Agenten ser din workspace – instant-mesh, nft-arbitrage, logs, CHECKLIST – og kan læse/opsummere/foreslå ændringer. Ingen copy-paste af filer. |
| **Lad AI’en arbejde på faste tidspunkter** | Cron: BuildConductor kl. 08:00, InvestorScout man/ons 10:00, StatusWeaver kl. 20:00. De kører selv og skriver i logs + kan sende korte summaries til chatten. Du behøver ikke “nudge” hver gang. |
| **Én-off opgaver** | Du (eller et script) kører fx `run_build_conductor.ps1` eller `openclaw cron run <uuid>`. Så kører agenten den prompt og arbejder i det projekt. |
| **Skills = AI kan gøre mere end chat** | Fx GitHub-skill: “Lav et issue i repo X om Y” – agenten bruger din token og opretter det. Flere skills = flere ting den kan udføre uden at du selv går ind i værktøjerne. |
| **Ét sted for flere projekter** | Én gateway, én workspace. Instant Mesh, wallet, reklame-generator, dashboard – alt det samme “hjerne” kan læse og arbejde i, så du behøver ikke skifte kontekst manuelt. |

---

## Hvorfor det kan føles “til ingen verdens nytte”

- **Uden cron** er det “bare chat” – du skal selv trigge alt.  
- **Uden klare prompts og run-scripts** ved agenten ikke hvad “BuildConductor” eller “wallet-monitor” skal gøre.  
- **Uden at gatewayen kører** svarer den ikke, og cron kører ikke.

Så: OpenClaw er **infrastrukturen** – chat, planlægning, workspace, skills. **Værdien** kommer når du bruger det til:  
(1) at stille spørgsmål om dine projekter,  
(2) at lade cron køre agenterne så der sker noget hver dag,  
(3) at give den opgaver (spawn/cron run) og læse logs/dashboard bagefter.

---

## Én sætning

**OpenClaw er en AI der kender din workspace og kan køre på plan eller når du beder om det – via chat, cron eller spawn – så du får svar og arbejde uden at sidde og manuelt køre alt.**

Resten er hvad du lægger i den: prompts, jobs, skills og projekter.

---

## "Det gør jo intet" – hvad der rent faktisk sker

- **Gateway + cron:** Når gatewayen kører og cron-jobs er loadet, kører BuildConductor/InvestorScout/StatusWeaver på deres tidspunkter og skriver i `workspace/projects/instant-mesh/logs/`. Det er der allerede kommet indlæg fra (fx build-log 2026-02-28 21:10). Ingen popup – du skal åbne logs eller dashboard.
- **Uden gateway:** Der sker ingenting i chat/cron. Så det føles som "intet".
- **Én ting der altid kan køre:** `scripts\do-something-now.ps1` – skriver timestamp til `OPENCLAW-RAN.txt` i roden. Så du kan se at noget kørte. Du kan sætte det i Windows Planlægger eller køre det manuelt.
