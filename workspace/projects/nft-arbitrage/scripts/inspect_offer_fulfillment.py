"""Inspect both listing and offer fulfillment response structures."""
import httpx
import asyncio
import json

API_KEY = "e73089173e1e45c4b016310dd9996677"
WALLET = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"
BASE = "https://api.opensea.io"
HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
LIST_HEADERS = {"accept": "application/json", "x-api-key": API_KEY}

async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        # Get fresh listing + bid for cryptocoven
        r1 = await client.get(f"{BASE}/api/v2/listings/collection/cryptocoven/all",
                              headers=LIST_HEADERS, params={"limit": 1})
        listings = r1.json().get("listings", [])

        r2 = await client.get(f"{BASE}/api/v2/offers/collection/cryptocoven",
                              headers=LIST_HEADERS, params={"limit": 5})
        offers = r2.json().get("offers", [])

        listing = listings[0]
        best_offer = max(offers, key=lambda o: int(o.get("price", {}).get("value", 0)))

        listing_hash = listing.get("order_hash")
        bid_hash = best_offer.get("order_hash")
        listing_protocol = listing.get("protocol_address")
        bid_protocol = best_offer.get("protocol_address")

        # Get listing token_id
        pd = listing.get("protocol_data", {}).get("parameters", {}).get("offer", [])
        token_id = pd[0].get("identifierOrCriteria", "1") if pd else "1"

        # LISTING FULFILLMENT
        print("=== LISTING FULFILLMENT ===")
        payload1 = {
            "listing": {"hash": listing_hash, "chain": "ethereum", "protocol_address": listing_protocol},
            "fulfiller": {"address": WALLET},
        }
        r3 = await client.post(f"{BASE}/api/v2/listings/fulfillment_data", headers=HEADERS, json=payload1)
        listing_tx = r3.json().get("fulfillment_data", {}).get("transaction", {})
        print(f"Keys: {list(listing_tx.keys())}")
        print(f"Function: {listing_tx.get('function', '')[:80]}")
        input_data = listing_tx.get("input_data")
        print(f"input_data type: {type(input_data)}")
        if isinstance(input_data, dict):
            print(f"input_data keys: {list(input_data.keys())}")

        # OFFER FULFILLMENT
        print("\n=== OFFER FULFILLMENT ===")
        payload2 = {
            "offer": {"hash": bid_hash, "chain": "ethereum", "protocol_address": bid_protocol},
            "fulfiller": {"address": WALLET},
            "consideration": {
                "asset_contract_address": "0x5180db8f5c931aae63c74266b211f580155ecac8",
                "token_id": str(token_id),
            },
        }
        r4 = await client.post(f"{BASE}/api/v2/offers/fulfillment_data", headers=HEADERS, json=payload2)
        offer_data = r4.json()
        offer_tx = offer_data.get("fulfillment_data", {}).get("transaction", {})
        print(f"Keys: {list(offer_tx.keys())}")
        print(f"Function: {offer_tx.get('function', '')[:80]}")
        input_data2 = offer_tx.get("input_data")
        print(f"input_data type: {type(input_data2)}")
        if isinstance(input_data2, dict):
            print(f"input_data keys: {list(input_data2.keys())}")

        # Full response dump
        print("\n=== FULL LISTING TX (first 1000 chars) ===")
        print(json.dumps(listing_tx, indent=2)[:1000])

        print("\n=== FULL OFFER TX (first 1500 chars) ===")
        print(json.dumps(offer_tx, indent=2)[:1500])

asyncio.run(main())
