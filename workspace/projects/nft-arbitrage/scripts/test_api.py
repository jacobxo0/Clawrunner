"""Quick test to verify OpenSea + Moralis API keys work."""

import asyncio
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

import httpx


async def test_opensea():
    print("=" * 50)
    print("Testing OpenSea API v2...")
    print("=" * 50)

    from src.config import get_settings
    settings = get_settings()
    api_key = settings.marketplace.opensea_api_key
    print(f"  Key loaded: {api_key[:10]}..." if api_key else "  WARNING: No OpenSea key!")

    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Test collection stats
        url = "https://api.opensea.io/api/v2/collections/pudgypenguins/stats"
        print(f"  GET {url}")
        resp = await client.get(url, headers=headers)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            total = data.get("total", {})
            print(f"  Floor: {total.get('floor_price', 'N/A')} ETH")
            print(f"  Volume: {total.get('volume', 'N/A')} ETH")
            print(f"  Owners: {total.get('num_owners', 'N/A')}")
            print("  -> OpenSea: OK")
        else:
            print(f"  Response: {resp.text[:500]}")


async def test_moralis():
    print()
    print("=" * 50)
    print("Testing Moralis API v2.2...")
    print("=" * 50)

    from src.config import get_settings
    settings = get_settings()
    api_key = settings.marketplace.moralis_api_key
    print(f"  Key loaded: {api_key[:10]}..." if api_key else "  WARNING: No Moralis key!")

    headers = {
        "accept": "application/json",
        "X-API-Key": api_key,
    }

    contract = "0xBd3531dA5CF5857e7CfAA92426877b022e612cf8"
    async with httpx.AsyncClient(timeout=15.0) as client:
        url = f"https://deep-index.moralis.io/api/v2.2/nft/{contract}/trades?chain=eth&limit=3"
        print(f"  GET {url}")
        resp = await client.get(url, headers=headers)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            trades = data.get("result", [])
            print(f"  Trades returned: {len(trades)}")
            if trades:
                price_wei = trades[0].get("price", "0")
                price_eth = int(price_wei) / 10**18 if price_wei != "0" else 0
                print(f"  Latest trade: {price_eth:.4f} ETH")
            print("  -> Moralis: OK")
        else:
            print(f"  Response: {resp.text[:500]}")


async def main():
    await test_opensea()
    await test_moralis()
    print()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
