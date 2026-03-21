"""Check current profitable spreads across all collections."""
import httpx
import asyncio

API_KEY = "e73089173e1e45c4b016310dd9996677"
HEADERS = {"accept": "application/json", "x-api-key": API_KEY}
BASE = "https://api.opensea.io"

COLLECTIONS = [
    {"slug": "based-onchain-dinos", "chain": "base", "royalty_bps": 500, "fee_bps": 250},
    {"slug": "cryptocoven", "chain": "ethereum", "royalty_bps": 500, "fee_bps": 250},
    {"slug": "tubby-cats", "chain": "ethereum", "royalty_bps": 500, "fee_bps": 250},
    {"slug": "opepen-edition", "chain": "ethereum", "royalty_bps": 500, "fee_bps": 250},
    {"slug": "nakamigos", "chain": "ethereum", "royalty_bps": 500, "fee_bps": 250},
    {"slug": "invisiblefriends", "chain": "ethereum", "royalty_bps": 500, "fee_bps": 250},
]

async def check_spread(client, col):
    slug = col["slug"]
    chain = col["chain"]
    royalty_bps = col["royalty_bps"]
    fee_bps = col["fee_bps"]
    total_fee_pct = (royalty_bps + fee_bps) / 10000
    gas_eth = 0.003 if chain == "ethereum" else 0.00005

    try:
        listings_r = await client.get(
            f"{BASE}/api/v2/listings/collection/{slug}/all",
            headers=HEADERS, params={"limit": 5},
        )
        offers_r = await client.get(
            f"{BASE}/api/v2/offers/collection/{slug}",
            headers=HEADERS, params={"limit": 10},
        )

        listings = listings_r.json().get("listings", []) if listings_r.status_code == 200 else []
        offers = offers_r.json().get("offers", []) if offers_r.status_code == 200 else []

        if not listings or not offers:
            print(f"  {slug} ({chain}): no data (listings={len(listings)} offers={len(offers)})")
            return

        cheapest_price = float("inf")
        for l in listings[:3]:
            p = l.get("price", {}).get("current", {})
            try:
                val = int(p.get("value", 0))
                dec = int(p.get("decimals", 18))
                price = val / (10**dec)
                if price < cheapest_price:
                    cheapest_price = price
            except:
                pass

        best_bid = 0
        for o in offers[:10]:
            p = o.get("price", {})
            try:
                val = int(p.get("value", 0))
                dec = int(p.get("decimals", 18))
                price = val / (10**dec)
                if price > best_bid and (cheapest_price <= 0 or price <= cheapest_price * 2.0):
                    best_bid = price
            except:
                pass

        if cheapest_price == float("inf") or best_bid == 0:
            print(f"  {slug} ({chain}): no valid prices")
            return

        gross = best_bid - cheapest_price
        fees = best_bid * total_fee_pct
        net = best_bid * (1 - total_fee_pct) - cheapest_price - gas_eth
        roi = (net / cheapest_price * 100) if cheapest_price > 0 else 0

        status = "PROFITABLE" if net > 0.001 else ("marginal" if net > 0 else "LOSS")
        print(f"  {slug} ({chain}): buy={cheapest_price:.5f} bid={best_bid:.5f} "
              f"gross={gross:.5f} fees={fees:.5f} gas={gas_eth:.5f} "
              f"net={net:.5f} roi={roi:.1f}% [{status}]")
    except Exception as e:
        print(f"  {slug}: ERROR {e}")

async def main():
    print("=== Current Spreads ===")
    async with httpx.AsyncClient(timeout=15) as client:
        for col in COLLECTIONS:
            await check_spread(client, col)
            await asyncio.sleep(0.3)

asyncio.run(main())
