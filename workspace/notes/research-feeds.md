# Research Feeds — hvad Ignis holder øje med

Bruges af `research-pulse` cron job (man+tor 08:00).
Agenten henter disse feeds, filtrerer relevant indhold, opsummerer og skriver til
`workspace/memory/research/YYYY-MM-DD.md`.

## AI / Agent-systemer (kerneområde)
- https://news.ycombinator.com/rss — HackerNews (AI, startups, tech)
- https://simonwillison.net/atom/everything/ — Simon Willison (LLM-praksis, tooling)
- https://www.deeplearning.ai/the-batch/feed/ — The Batch (AI nyheder, ugentlig)

## Crypto / DeFi (nft-arbitrage projekt)
- https://feeds.feedburner.com/CoinDesk — CoinDesk nyheder
- https://cointelegraph.com/rss — CoinTelegraph

## Dansk byggeri / regulering (Byggesagsassistenten)
- https://www.bolius.dk/feed — Bolius (bolignyheder DK)
- https://www.dr.dk/nyheder/penge/rss.xml — DR Penge (ejendom, økonomi)

## Filtrering
Agenten skal KUN gemme indhold der er relevant for mindst ét af disse emner:
1. LLM-fremskridt, agent-frameworks, tool-use, memory-systemer
2. NFT/DeFi arbitrage, on-chain data, gas-priser
3. Dansk byggeret, BR18/AB18, byggetilladelser
4. Startup-funding, SaaS-vækst (Instant Mesh)

Irrelevant indhold springes over. Max 5 bullets per feed per kørsel.
