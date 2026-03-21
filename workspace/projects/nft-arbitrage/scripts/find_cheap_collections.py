"""Find ultra-cheap, actively traded NFT collections on OpenSea."""
import httpx
import time
import sys

API_KEY = "e73089173e1e45c4b016310dd9996677"
HEADERS = {"accept": "application/json", "x-api-key": API_KEY}
BASE = "https://api.opensea.io/api/v2"

MAX_FLOOR = 0.05
MIN_FLOOR = 0.001

ALREADY = {
    "cryptocoven", "tubby-cats", "based-onchain-dinos",
    "opepen-edition", "invisiblefriends", "nakamigos",
    "azuki", "milady", "pudgypenguins",
}


def fetch_collections(page_cursor=None):
    params = {"chain": "ethereum", "order_by": "seven_day_volume", "limit": 50}
    if page_cursor:
        params["next"] = page_cursor
    r = httpx.get(f"{BASE}/collections", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_stats(slug):
    try:
        r = httpx.get(f"{BASE}/collections/{slug}/stats", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            s = r.json().get("total", {})
            return float(s.get("floor_price", 0) or 0), float(s.get("volume", 0) or 0)
    except Exception:
        pass
    return 0, 0


def main():
    print("Scanning OpenSea for cheap, active collections...", flush=True)
    cheap = []
    cursor = None

    for page in range(8):
        print(f"\n--- Page {page+1} ---", flush=True)
        try:
            data = fetch_collections(cursor)
        except Exception as e:
            print(f"  Fetch error: {e}", flush=True)
            break

        cols = data.get("collections", [])
        cursor = data.get("next")

        for c in cols:
            slug = c.get("collection", "")
            name = c.get("name", slug)
            contracts = c.get("contracts", [])
            if not contracts or not slug or slug in ALREADY:
                continue

            addr = contracts[0].get("address", "")
            chain = contracts[0].get("chain", "ethereum")

            floor, vol = fetch_stats(slug)
            time.sleep(0.28)

            if MIN_FLOOR <= floor <= MAX_FLOOR:
                cheap.append(dict(slug=slug, name=name, contract=addr, chain=chain, floor=floor, volume=vol))
                print(f"  HIT  {slug:35s} floor={floor:.4f} ETH  vol={vol:.0f}", flush=True)
            elif floor > 0:
                print(f"  skip {slug:35s} floor={floor:.4f}", flush=True)
            else:
                print(f"  skip {slug:35s} (no floor)", flush=True)

            if len(cheap) >= 15:
                break

        if len(cheap) >= 15 or not cursor:
            break

    print(f"\n{'='*70}")
    print(f"FOUND {len(cheap)} collections with floor {MIN_FLOOR}-{MAX_FLOOR} ETH")
    print(f"{'='*70}")
    for c in sorted(cheap, key=lambda x: x["floor"]):
        print(f'  - slug: "{c["slug"]}"')
        print(f'    name: "{c["name"]}"')
        print(f'    chain: "{c["chain"]}"')
        print(f'    contract: "{c["contract"]}"')
        print(f"    royalty_bps: 500")
        print(f"    marketplace_fee_bps: 250")
        print(f"    active: true")
        print()


if __name__ == "__main__":
    main()
