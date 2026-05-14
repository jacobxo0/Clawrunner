# Jina Reader — læs enhver URL som ren tekst

Konverterer enhver webside til læsbar markdown. Perfekt til at læse artikler,
dokumentation, konkurrenters sider og nyhedshistorier uden at håndtere HTML.

## Brug (ingen API-nøgle nødvendig)

```
GET https://r.jina.ai/<url>
```

Eksempel:
```
GET https://r.jina.ai/https://techcrunch.com/2026/05/14/ai-agents-funding/
```

## Kald via ai-core

```json
POST ${AI_CORE_URL}/command
{
  "command": "fetch_url",
  "arguments": {
    "url": "https://r.jina.ai/https://example.com/article"
  }
}
```

Returnerer artiklens tekst som markdown — klar til at opsummere eller citere.

## Med højere rate limit (valgfrit)

Tilføj `Authorization: Bearer ${JINA_API_KEY}` header hvis du har en nøgle.
Gratis tier uden nøgle: ~200 req/dag — mere end nok til research-jobs.

## Hvornår bruges den

- Læs en specifik artikel Tavily fandt (følg op på URL fra søgeresultat)
- Scrape konkurrenters prissider, Om os, features
- Læs investor-profiler og LinkedIn-lignende sider
- Hent dokumentation for et API eller framework

## Workflow: Tavily + Jina

```
1. Tavily søger → returnerer 5 URLs med snippets
2. Vælg de 2-3 mest relevante URLs
3. Jina læser dem fuldt ud
4. Opsummer med Haiku
```
