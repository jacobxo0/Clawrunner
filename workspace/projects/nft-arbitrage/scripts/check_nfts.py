"""Check if wallet is holding any NFTs (bought but not sold)."""
import httpx
import os
from dotenv import load_dotenv
load_dotenv()

MORALIS_KEY = os.getenv("MORALIS_API_KEY", "")
OPENSEA_KEY = os.getenv("OPENSEA_API_KEY", "")
WALLET = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"


def check_opensea():
    print("=== Checking OpenSea for NFTs in wallet ===")
    headers = {"accept": "application/json", "x-api-key": OPENSEA_KEY}
    url = f"https://api.opensea.io/api/v2/chain/ethereum/account/{WALLET}/nfts"
    resp = httpx.get(url, headers=headers, params={"limit": 50}, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        nfts = data.get("nfts", [])
        if nfts:
            print(f"  Found {len(nfts)} NFTs in wallet:")
            for nft in nfts:
                name = nft.get("name", "Unknown")
                collection = nft.get("collection", "?")
                token_id = nft.get("identifier", "?")
                print(f"    - {collection} #{token_id}: {name}")
        else:
            print("  No NFTs found in wallet")
    else:
        print(f"  OpenSea error: {resp.status_code}")


def check_moralis():
    print("\n=== Checking Moralis for NFTs in wallet ===")
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    url = f"https://deep-index.moralis.io/api/v2.2/{WALLET}/nft"
    resp = httpx.get(url, headers=headers, params={"chain": "eth", "limit": 50}, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        nfts = data.get("result", [])
        if nfts:
            print(f"  Found {len(nfts)} NFTs in wallet:")
            for nft in nfts:
                name = nft.get("name", "Unknown collection")
                token_id = nft.get("token_id", "?")
                contract = nft.get("token_address", "?")[:20]
                print(f"    - {name} #{token_id} ({contract}...)")
        else:
            print("  No NFTs found in wallet")
    else:
        print(f"  Moralis error: {resp.status_code}")


def check_etherscan_txs():
    print("\n=== Recent transactions via Etherscan ===")
    url = f"https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": WALLET,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 20,
        "sort": "desc",
        "apikey": "YourApiKeyToken",
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            txs = data.get("result", [])
            if isinstance(txs, list):
                total_gas_eth = 0
                for tx in txs:
                    gas_price = int(tx.get("gasPrice", 0))
                    gas_used = int(tx.get("gasUsed", 0))
                    gas_cost_wei = gas_price * gas_used
                    gas_cost_eth = gas_cost_wei / 1e18
                    total_gas_eth += gas_cost_eth
                    value_eth = int(tx.get("value", 0)) / 1e18
                    is_error = tx.get("isError", "0")
                    func = tx.get("functionName", "")[:40]
                    tx_hash = tx.get("hash", "")[:16]
                    direction = "OUT" if tx.get("from", "").lower() == WALLET.lower() else "IN"
                    print(f"  {direction} | {value_eth:.5f} ETH | gas {gas_cost_eth:.6f} | err={is_error} | {func} | {tx_hash}")
                print(f"\n  Total gas in last {len(txs)} txs: {total_gas_eth:.6f} ETH (${total_gas_eth * 1980:.2f})")
    except Exception as e:
        print(f"  Etherscan error: {e}")


if __name__ == "__main__":
    check_opensea()
    check_moralis()
    check_etherscan_txs()
