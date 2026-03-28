# BYGGESAGSASSISTENTEN — Produktkontekst for Ignis

Dette er Jacobs primære SaaS-produkt under udvikling. Brug denne fil til at hjælpe med markedsføring, salg, strategi og kommunikation om produktet.

---

## Hvad er det?

**Byggesagsassistenten** er en AI-drevet desktop-platform til danske bygherrerådgivere og bygningskonstruktører. Den hjælper med at udarbejde professionelle **byggesagsbeskrivelser** — de juridisk og fagligt forankrede dokumenter der definerer en byggesag fra A til Z.

Platformen er ikke en generisk dokumentgenerator. Den er dybt forankret i:
- **AB18** — Almindelige Betingelser for bygge- og anlægsvirksomhed 2018
- **ABT18** — Almindelige Betingelser for Totalentreprise 2018
- **BR18** — Bygningsreglementet 2018

AI-assistenten i produktet genererer indhold med structured outputs (aldrig fri tekst) og validerer altid paragrafhenvisninger mod de kanoniske standarder.

---

## Målgruppe

**Primær:** Bygherrerådgivere og bygningskonstruktører i rådgivende ingeniørvirksomheder
**Sekundær:** Større entreprenørvirksomheder der laver egne byggesagsbeskrivelser
**Markedsstørrelse:** Ca. 3.500 aktive rådgivningsvirksomheder i Danmark + ca. 800 større entreprenører

**Bruger-persona:** Lars, 42 år, bygningskonstruktør hos en rådgivende virksomhed med 8 ansatte. Bruger i dag Word-skabeloner fra foreningen. Bruger 4-8 timer per byggesagsbeskrivelse. Hader at finde rundt i AB18-paragraffer.

---

## Kerneværdi (sælg dette)

> "Fra 6 timers copy-paste i Word til 45 minutter med præcis, juridisk korrekt output."

- Juridisk sikkerhed: AI hallucinerer ALDRIG paragrafindhold — alt §-indhold hentes fra de kanoniske standarder
- Struktureret workflow: 8 sektioner i fast faglig rækkefølge
- Teamsamarbejde: Bygherrerådgiver + entreprenør deler samme dokument
- Revisionshistorik: Alle ændringer er sporet med hvem, hvad og hvornår

---

## Forretningsmodel

| Plan | Pris (estimat) | Målgruppe |
|------|---------------|-----------|
| TRIAL | Gratis, 2 projekter | Prøveperiode |
| STARTER | 499 kr/md | Solo-rådgiver |
| PROFESSIONAL | 1.499 kr/md | Team op til 20 |
| ENTERPRISE | Aftalt | Større virksomheder |

Betaling via Stripe. Fakturering månedlig eller årlig (-20%).

---

## Tech stack (til reference)

- Desktop-app: Tauri 2 + React (Windows + Mac)
- Backend: Fastify + PostgreSQL + Redis
- AI: Claude 3.5 Sonnet via Anthropic API
- Dokumentlager: Cloudflare R2
- Email: Resend
- Status: Under aktiv udvikling

---

## Markedskanaler (brainstorm — ikke bekræftet)

1. **Direkte salg til rådgivende ingeniørvirksomheder** — LinkedIn outreach til bygningskonstruktører og projektledere
2. **Partnerkanaler** — samarbejde med foreninger (FRI, Bygherreforeningen, Dansk Byggeri)
3. **Content marketing** — faglige artikler om AB18/ABT18 fortolkning, byggesagsprocessen
4. **Demo-webinarer** — "Lav en komplet byggesagsbeskrivelse på 45 min"
5. **Word-of-mouth** — byggebranchen er lille, anbefalinger driver meget

---

## Hvad Ignis kan hjælpe med

- Udkast til LinkedIn-opslag, posts, artikler om produktet
- Strategi for go-to-market og prismodel
- Mails til potentielle kunder eller partnere
- Konkurrentanalyse (hvad bruger branchen i dag?)
- Pitchdæk-indhold og investorargumenter
- Svar på spørgsmål om AB18/ABT18 i markedsføringskontekst
- Hjælp til at formulere USP'er og value propositions

---

## Hvad Ignis IKKE skal gøre

- Kode på selve Byggesagsassistenten-projektet (det klarer Jacob selv)
- Fortolke AB18/ABT18 juridisk bindende (altid anbefal faglig rådgivning)
- Sende markedsføringskommunikation uden Jacobs godkendelse
