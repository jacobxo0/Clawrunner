"""Test the Seaport encoder with real fulfillment data."""
import sys
sys.path.insert(0, ".")

import httpx
import asyncio
import json

API_KEY = "e73089173e1e45c4b016310dd9996677"
WALLET = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"
BASE = "https://api.opensea.io"
HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
LIST_HEADERS = {"accept": "application/json", "x-api-key": API_KEY}

async def main():
    from src.execution.seaport_encoder import encode_fulfillment_tx

    async with httpx.AsyncClient(timeout=15) as client:
        # Get fresh listing for cryptocoven
        r1 = await client.get(f"{BASE}/api/v2/listings/collection/cryptocoven/all",
                              headers=LIST_HEADERS, params={"limit": 1})
        listing = r1.json()["listings"][0]
        listing_hash = listing["order_hash"]
        listing_protocol = listing["protocol_address"]

        # Get best bid
        r2 = await client.get(f"{BASE}/api/v2/offers/collection/cryptocoven",
                              headers=LIST_HEADERS, params={"limit": 5})
        offers = r2.json()["offers"]
        best_offer = max(offers, key=lambda o: int(o.get("price", {}).get("value", 0)))
        bid_hash = best_offer["order_hash"]
        bid_protocol = best_offer["protocol_address"]

        # Token ID from listing
        pd = listing.get("protocol_data", {}).get("parameters", {}).get("offer", [])
        token_id = pd[0].get("identifierOrCriteria", "1") if pd else "1"

        # Test 1: Encode listing fulfillment
        print("=== Test 1: Listing Fulfillment Encoding ===")
        payload1 = {
            "listing": {"hash": listing_hash, "chain": "ethereum", "protocol_address": listing_protocol},
            "fulfiller": {"address": WALLET},
        }
        r3 = await client.post(f"{BASE}/api/v2/listings/fulfillment_data", headers=HEADERS, json=payload1)
        listing_tx = r3.json().get("fulfillment_data", {}).get("transaction", {})

        try:
            calldata = encode_fulfillment_tx(listing_tx)
            print(f"  Calldata length: {len(calldata)} bytes")
            print(f"  Selector: 0x{calldata[:4].hex()}")
            print(f"  First 100 bytes: 0x{calldata[:100].hex()}")
            print(f"  SUCCESS!")
        except Exception as e:
            print(f"  FAILED: {e}")

        # Test 2: Encode offer fulfillment
        print("\n=== Test 2: Offer Fulfillment Encoding ===")
        payload2 = {
            "offer": {"hash": bid_hash, "chain": "ethereum", "protocol_address": bid_protocol},
            "fulfiller": {"address": WALLET},
            "consideration": {
                "asset_contract_address": "0x5180db8f5c931aae63c74266b211f580155ecac8",
                "token_id": str(token_id),
            },
        }
        r4 = await client.post(f"{BASE}/api/v2/offers/fulfillment_data", headers=HEADERS, json=payload2)
        offer_tx = r4.json().get("fulfillment_data", {}).get("transaction", {})

        try:
            calldata2 = encode_fulfillment_tx(offer_tx)
            print(f"  Calldata length: {len(calldata2)} bytes")
            print(f"  Selector: 0x{calldata2[:4].hex()}")
            print(f"  First 100 bytes: 0x{calldata2[:100].hex()}")
            print(f"  SUCCESS!")
        except Exception as e:
            print(f"  FAILED: {e}")

asyncio.run(main())
