"""Find very cheap Ethereum NFT collections with bid activity."""
import asyncio, sys, os
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv(override=True)
import httpx

API_KEY = os.getenv("OPENSEA_API_KEY", "")
BASE = "https://api.opensea.io"
HEADERS = {"accept": "application/json", "x-api-key": API_KEY}

CHEAP_CANDIDATES = [
    "creepz-genesis",
    "cool-cats-nft",
    "world-of-women-nft",
    "doodles-official",
    "nakamigos",
    "rektguy",
    "pixelmon-generation-1",
    "meebits",
    "cryptoadz-by-gremplin",
    "mfers",
    "tubby-cats",
    "loot-for-adventurers",
    "nouns",
    "cryptodickbutts-s3",
    "invisiblefriends",
    "the-memes-by-6529",
    "based-onchain-dinos",
    "terraforms",
    "cryptocoven",
    "clonex",
]

async def check(slug):
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(f"{BASE}/api/v2/collections/{slug}/stats", headers=HEADERS)
            if r.status_code != 200:
                return None
            total = r.json().get("total", {})
            floor = float(total.get("floor_price", 0) or 0)
            volume = float(total.get("volume", 0) or 0)
            
            r2 = await client.get(f"{BASE}/api/v2/offers/collection/{slug}?limit=5", headers=HEADERS)
            bids = r2.json().get("offers", []) if r2.status_code == 200 else []
            
            best_bid = 0
            for b in bids:
                p = b.get("price", {})
                try:
                    val = int(p.get("value", "0"))
                    dec = int(p.get("decimals", 18))
                    bp = val / (10**dec)
                    if bp > best_bid:
                        best_bid = bp
                except:
                    pass
            
            return {"slug": slug, "floor": floor, "best_bid": best_bid, "volume": volume, "bids": len(bids)}
        except:
            return None

async def main():
    results = []
    for slug in CHEAP_CANDIDATES:
        r = await check(slug)
        if r and r["floor"] > 0:
            results.append(r)
            emoji = "+" if r["best_bid"] > r["floor"] else "-"
            print(f"  {r['slug']:30s} floor={r['floor']:.4f} bid={r['best_bid']:.4f} bids={r['bids']} vol={r['volume']:.0f} {emoji}")
        await asyncio.sleep(0.3)
    
    print(f"\n--- Sorted by floor price (cheapest first) ---")
    for r in sorted(results, key=lambda x: x["floor"]):
        affordable = "OK" if r["floor"] <= 0.025 else ""
        print(f"  {r['slug']:30s} floor={r['floor']:.4f} bid={r['best_bid']:.4f} {affordable}")

asyncio.run(main())
