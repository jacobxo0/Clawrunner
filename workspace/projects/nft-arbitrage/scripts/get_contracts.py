import httpx, asyncio, json

API_KEY = "e73089173e1e45c4b016310dd9996677"
HEADERS = {"accept": "application/json", "x-api-key": API_KEY}
BASE = "https://api.opensea.io"

slugs = [
    "based-onchain-dinos", "tubby-cats", "cryptocoven", "milady",
    "azuki", "pudgypenguins", "nakamigos", "invisiblefriends", "opepen-edition",
]

async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        for slug in slugs:
            try:
                r = await client.get(f"{BASE}/api/v2/collections/{slug}", headers=HEADERS)
                if r.status_code == 200:
                    data = r.json()
                    contracts = data.get("contracts", [])
                    print(f"{slug}:")
                    for c in contracts:
                        chain = c.get("chain", "?")
                        addr = c.get("address", "?")
                        print(f"  chain={chain} address={addr}")
                    if not contracts:
                        print("  NO CONTRACTS IN RESPONSE")
                        print(f"  keys: {list(data.keys())}")
                else:
                    print(f"{slug}: HTTP {r.status_code}")
            except Exception as e:
                print(f"{slug}: error {e}")

asyncio.run(main())
