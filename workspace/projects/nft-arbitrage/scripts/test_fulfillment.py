"""Test that we can actually get fulfillment data for fresh listings/bids."""
import httpx
import asyncio

API_KEY = "e73089173e1e45c4b016310dd9996677"
WALLET = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"
BASE = "https://api.opensea.io"
HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
LIST_HEADERS = {"accept": "application/json", "x-api-key": API_KEY}

async def test_collection(slug, chain, contract):
    print(f"\n=== {slug} ({chain}) ===")
    async with httpx.AsyncClient(timeout=15) as client:
        # Get fresh listings
        r1 = await client.get(
            f"{BASE}/api/v2/listings/collection/{slug}/all",
            headers=LIST_HEADERS, params={"limit": 3},
        )
        listings = r1.json().get("listings", []) if r1.status_code == 200 else []
        if not listings:
            print("  No listings found!")
            return

        listing = listings[0]
        listing_hash = listing.get("order_hash", "")
        listing_protocol = listing.get("protocol_address", "")
        price_obj = listing.get("price", {}).get("current", {})
        try:
            val = int(price_obj.get("value", 0))
            dec = int(price_obj.get("decimals", 18))
            price = val / (10**dec)
        except:
            price = 0
        print(f"  Listing: price={price:.5f} hash={listing_hash[:20]} protocol={listing_protocol[:20]}")

        # Get fresh bids
        r2 = await client.get(
            f"{BASE}/api/v2/offers/collection/{slug}",
            headers=LIST_HEADERS, params={"limit": 5},
        )
        offers = r2.json().get("offers", []) if r2.status_code == 200 else []
        if not offers:
            print("  No offers found!")
            return

        best = max(offers, key=lambda o: int(o.get("price", {}).get("value", 0)))
        bid_hash = best.get("order_hash", "")
        bid_protocol = best.get("protocol_address", "")
        bp = best.get("price", {})
        try:
            bval = int(bp.get("value", 0))
            bdec = int(bp.get("decimals", 18))
            bid_price = bval / (10**bdec)
        except:
            bid_price = 0
        criteria = best.get("criteria", {})
        print(f"  Best bid: price={bid_price:.5f} hash={bid_hash[:20]} protocol={bid_protocol[:20]}")
        print(f"  Bid criteria: trait={criteria.get('trait')} ids={criteria.get('encoded_token_ids', '?')[:20]}")

        # Test listing fulfillment
        print(f"\n  Testing listing fulfillment ({chain})...")
        payload1 = {
            "listing": {"hash": listing_hash, "chain": chain, "protocol_address": listing_protocol},
            "fulfiller": {"address": WALLET},
        }
        r3 = await client.post(f"{BASE}/api/v2/listings/fulfillment_data", headers=HEADERS, json=payload1)
        print(f"  Listing fulfillment: {r3.status_code} - {r3.text[:200]}")

        # Test offer fulfillment
        token_id = "1"  # dummy - just testing API access
        pd = listing.get("protocol_data", {}).get("parameters", {}).get("offer", [])
        if pd:
            token_id = pd[0].get("identifierOrCriteria", "1")
        print(f"\n  Testing offer fulfillment (token_id={token_id})...")
        payload2 = {
            "offer": {"hash": bid_hash, "chain": chain, "protocol_address": bid_protocol},
            "fulfiller": {"address": WALLET},
            "consideration": {"asset_contract_address": contract, "token_id": str(token_id)},
        }
        r4 = await client.post(f"{BASE}/api/v2/offers/fulfillment_data", headers=HEADERS, json=payload2)
        print(f"  Offer fulfillment: {r4.status_code} - {r4.text[:200]}")

async def main():
    await test_collection("cryptocoven", "ethereum", "0x5180db8f5c931aae63c74266b211f580155ecac8")
    await asyncio.sleep(0.5)
    await test_collection("tubby-cats", "ethereum", "0xca7ca7bcc765f77339be2d648ba53ce9c8a262bd")
    await asyncio.sleep(0.5)
    await test_collection("based-onchain-dinos", "base", "0xd4c5292b9689238f0a51c8505b1d1d6714ce95a0")

asyncio.run(main())
