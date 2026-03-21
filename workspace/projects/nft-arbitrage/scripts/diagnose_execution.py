"""Diagnose WHY the fulfillment API fails."""
import asyncio
import httpx
import sqlite3
import json

API_KEY = "e73089173e1e45c4b016310dd9996677"
WALLET = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"
BASE = "https://api.opensea.io"
HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

async def main():
    # Get a recent opportunity from the DB
    conn = sqlite3.connect("nft_arbitrage.db")
    c = conn.cursor()
    c.execute("""
        SELECT o.listing_order_hash, o.bid_order_hash, o.token_id,
               o.buy_price, o.expected_exit, o.collection_id,
               col.slug, col.contract_address
        FROM opportunities o
        LEFT JOIN collections col ON o.collection_id = col.id
        WHERE o.listing_order_hash != '' AND o.bid_order_hash != ''
        ORDER BY o.created_at DESC LIMIT 1
    """)
    row = c.fetchone()
    conn.close()

    if not row:
        print("No opportunities with order hashes found!")
        return

    listing_hash, bid_hash, token_id, buy_price, exit_price, col_id, slug, contract = row
    print(f"Testing with: {slug} token#{token_id}")
    print(f"  listing_hash: {listing_hash}")
    print(f"  bid_hash: {bid_hash}")
    print(f"  contract: {contract}")
    print(f"  buy: {buy_price} -> sell: {exit_price}")
    print()

    async with httpx.AsyncClient(timeout=15) as client:
        # Test 1: Is the listing still active?
        print("=== TEST 1: Check listing fulfillment ===")
        payload = {
            "listing": {
                "hash": listing_hash,
                "chain": "ethereum",
                "protocol_address": "0x0000000000000068F116a894984e2DB1123eB395",
            },
            "fulfiller": {
                "address": WALLET,
            },
        }
        print(f"  POST /api/v2/listings/fulfillment_data")
        print(f"  Payload: {json.dumps(payload, indent=2)}")
        try:
            resp = await client.post(
                f"{BASE}/api/v2/listings/fulfillment_data",
                headers=HEADERS,
                json=payload,
            )
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {resp.text[:1000]}")
        except Exception as e:
            print(f"  Error: {e}")

        print()

        # Test 2: Is the bid still active?
        print("=== TEST 2: Check offer fulfillment ===")
        payload2 = {
            "offer": {
                "hash": bid_hash,
                "chain": "ethereum",
                "protocol_address": "0x0000000000000068F116a894984e2DB1123eB395",
            },
            "fulfiller": {
                "address": WALLET,
            },
            "consideration": {
                "asset_contract_address": contract,
                "token_id": str(token_id),
            },
        }
        print(f"  POST /api/v2/offers/fulfillment_data")
        print(f"  Payload: {json.dumps(payload2, indent=2)}")
        try:
            resp2 = await client.post(
                f"{BASE}/api/v2/offers/fulfillment_data",
                headers=HEADERS,
                json=payload2,
            )
            print(f"  Status: {resp2.status_code}")
            print(f"  Response: {resp2.text[:1000]}")
        except Exception as e:
            print(f"  Error: {e}")

        print()

        # Test 3: What bids are actually active?
        print("=== TEST 3: Current best bids ===")
        try:
            resp3 = await client.get(
                f"{BASE}/api/v2/offers/collection/{slug}",
                headers={"accept": "application/json", "x-api-key": API_KEY},
                params={"limit": 5},
            )
            if resp3.status_code == 200:
                data = resp3.json()
                offers = data.get("offers", [])
                print(f"  Active offers: {len(offers)}")
                for o in offers[:3]:
                    price_obj = o.get("price", {})
                    try:
                        val = int(price_obj.get("value", 0))
                        dec = int(price_obj.get("decimals", 18))
                        price = val / (10**dec)
                    except:
                        price = 0
                    criteria = o.get("criteria", {})
                    print(f"    price={price:.6f} hash={o.get('order_hash','')[:16]} "
                          f"protocol={o.get('protocol_address','')[:16]} "
                          f"criteria={criteria}")
            else:
                print(f"  Error: {resp3.status_code} {resp3.text[:200]}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 4: Current listings
        print()
        print("=== TEST 4: Current cheapest listings ===")
        try:
            resp4 = await client.get(
                f"{BASE}/api/v2/listings/collection/{slug}/all",
                headers={"accept": "application/json", "x-api-key": API_KEY},
                params={"limit": 3},
            )
            if resp4.status_code == 200:
                data = resp4.json()
                listings = data.get("listings", [])
                print(f"  Active listings: {len(listings)}")
                for l in listings[:3]:
                    price = l.get("price", {}).get("current", {})
                    try:
                        val = int(price.get("value", 0))
                        dec = int(price.get("decimals", 18))
                        p = val / (10**dec)
                    except:
                        p = 0
                    print(f"    price={p:.6f} hash={l.get('order_hash','')[:16]} "
                          f"protocol={l.get('protocol_address','')[:16]}")
            else:
                print(f"  Error: {resp4.status_code} {resp4.text[:200]}")
        except Exception as e:
            print(f"  Error: {e}")

asyncio.run(main())
