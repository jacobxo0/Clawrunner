"""Inspect the actual structure of OpenSea fulfillment response."""
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
        # Get a fresh listing for cryptocoven
        r = await client.get(
            f"{BASE}/api/v2/listings/collection/cryptocoven/all",
            headers=LIST_HEADERS, params={"limit": 1},
        )
        listings = r.json().get("listings", [])
        if not listings:
            print("No listings!")
            return

        listing = listings[0]
        listing_hash = listing.get("order_hash", "")
        listing_protocol = listing.get("protocol_address", "")
        print(f"Listing hash: {listing_hash}")

        # Get fulfillment data
        payload = {
            "listing": {"hash": listing_hash, "chain": "ethereum", "protocol_address": listing_protocol},
            "fulfiller": {"address": WALLET},
        }
        r2 = await client.post(f"{BASE}/api/v2/listings/fulfillment_data", headers=HEADERS, json=payload)
        if r2.status_code != 200:
            print(f"Error: {r2.status_code} {r2.text[:200]}")
            return

        data = r2.json()
        tx = data.get("fulfillment_data", {}).get("transaction", {})

        print("\n=== Transaction object keys ===")
        print(list(tx.keys()))

        print("\n=== function ===")
        print(tx.get("function", "N/A"))

        print("\n=== to ===")
        print(tx.get("to", "N/A"))

        print("\n=== value ===")
        print(tx.get("value", "N/A"))

        input_data = tx.get("input_data", None)
        print("\n=== input_data type ===")
        print(type(input_data))

        if isinstance(input_data, str):
            print(f"\n=== input_data (hex string, first 200 chars) ===")
            print(input_data[:200])
        elif isinstance(input_data, dict):
            print(f"\n=== input_data (dict keys) ===")
            print(list(input_data.keys()))
            print(f"\n=== input_data (full, first 500 chars) ===")
            print(json.dumps(input_data, indent=2)[:500])
        elif isinstance(input_data, list):
            print(f"\n=== input_data is a list of length {len(input_data)} ===")
            print(json.dumps(input_data[:2], indent=2)[:500])
        else:
            print(f"\n=== input_data value ===")
            print(str(input_data)[:500])

asyncio.run(main())
