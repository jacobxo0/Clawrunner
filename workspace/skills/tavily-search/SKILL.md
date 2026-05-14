# Tavily Search — AI-native websøgning

Brug dette når du skal søge på nettet og have præcise, opsummerede svar med kilder.
Langt bedre end Brave til research-opgaver — returnerer snippets klar til brug.

## Endpoint

```
POST https://api.tavily.com/search
Content-Type: application/json
Authorization: Bearer ${TAVILY_API_KEY}
```

## Request

```json
{
  "query": "din søgeforespørgsel",
  "search_depth": "basic",
  "max_results": 5,
  "include_answer": true
}
```

- `search_depth`: `"basic"` (hurtig, billig) eller `"advanced"` (dybere, 2 credits)
- `include_answer`: `true` giver en AI-opsummering oven på resultaterne
- `max_results`: 3-5 er nok til de fleste opgaver

## Kald via ai-core

```json
POST ${AI_CORE_URL}/command
{
  "command": "fetch_url",
  "arguments": {
    "url": "https://api.tavily.com/search",
    "method": "POST",
    "headers": { "Authorization": "Bearer ${TAVILY_API_KEY}", "Content-Type": "application/json" },
    "body": { "query": "...", "search_depth": "basic", "max_results": 5, "include_answer": true }
  }
}
```

## Svar-format

```json
{
  "answer": "AI-genereret svar på spørgsmålet",
  "results": [
    { "title": "...", "url": "...", "content": "snippet...", "score": 0.95 }
  ]
}
```

## Hvornår bruges den

- Research til investor pitch, markedsanalyse, konkurrentanalyse
- Faktacheck inden tekst skrives
- Nyheder om specifikke emner (kombiner med research-feeds)
- Dyb research: kør `search_depth: "advanced"` (koster 2 credits i stedet for 1)

## Gratis tier

1.000 søgninger/måned. Brug `basic` som default — spar `advanced` til vigtige opgaver.
