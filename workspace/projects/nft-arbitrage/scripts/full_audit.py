"""Full audit: where did the money go? Check all on-chain transactions."""
import httpx
import os
from dotenv import load_dotenv
load_dotenv()

MORALIS_KEY = os.getenv("MORALIS_API_KEY", "")
WALLET = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"


def get_all_transactions():
    """Get full transaction history from Moralis."""
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    url = f"https://deep-index.moralis.io/api/v2.2/{WALLET}"
    params = {"chain": "eth", "limit": 100}

    resp = httpx.get(url, headers=headers, params=params, timeout=20)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text[:200]}")
        return []
    return resp.json().get("result", [])


def get_erc20_transfers():
    """Get all ERC20 (WETH) transfers."""
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    url = f"https://deep-index.moralis.io/api/v2.2/{WALLET}/erc20/transfers"
    params = {"chain": "eth", "limit": 100}

    resp = httpx.get(url, headers=headers, params=params, timeout=20)
    if resp.status_code != 200:
        return []
    return resp.json().get("result", [])


def main():
    print("=" * 80)
    print("FULL WALLET AUDIT")
    print(f"Wallet: {WALLET}")
    print("=" * 80)

    txs = get_all_transactions()
    print(f"\nFound {len(txs)} transactions\n")

    total_gas_eth = 0
    total_sent_eth = 0
    total_received_eth = 0

    for tx in reversed(txs):
        block_time = tx.get("block_timestamp", "?")[:19]
        tx_hash = tx.get("hash", "")[:16]
        from_addr = tx.get("from_address", "").lower()
        to_addr = tx.get("to_address", "").lower()
        value_wei = int(tx.get("value", "0"))
        value_eth = value_wei / 1e18
        gas_price = int(tx.get("gas_price", "0"))
        receipt_gas = int(tx.get("receipt_gas_used", "0"))
        gas_cost_eth = (gas_price * receipt_gas) / 1e18

        is_outgoing = from_addr == WALLET.lower()
        direction = "OUT" if is_outgoing else "IN "

        if is_outgoing:
            total_gas_eth += gas_cost_eth
            total_sent_eth += value_eth
        else:
            total_received_eth += value_eth

        func = tx.get("method_label", "") or ""
        print(f"  {block_time} | {direction} | val={value_eth:>10.5f} ETH | gas={gas_cost_eth:.6f} | {func[:30]:30s} | {tx_hash}")

    print()
    print("=" * 80)
    print(f"  Total ETH received (deposits):   {total_received_eth:.6f} ETH  (${total_received_eth * 1980:.2f})")
    print(f"  Total ETH sent out:              {total_sent_eth:.6f} ETH  (${total_sent_eth * 1980:.2f})")
    print(f"  Total gas burned:                {total_gas_eth:.6f} ETH  (${total_gas_eth * 1980:.2f})")
    print(f"  Net flow:                        {total_received_eth - total_sent_eth - total_gas_eth:.6f} ETH")
    print("=" * 80)

    print("\n--- ERC20 (WETH) transfers ---")
    transfers = get_erc20_transfers()
    for t in reversed(transfers):
        ts = t.get("block_timestamp", "?")[:19]
        from_a = t.get("from_address", "")[:10]
        to_a = t.get("to_address", "")[:10]
        val = int(t.get("value", "0")) / 1e18
        token = t.get("token_symbol", "?")
        direction = "OUT" if t.get("from_address", "").lower() == WALLET.lower() else "IN "
        print(f"  {ts} | {direction} | {val:.6f} {token} | from={from_a}.. to={to_a}..")

    print()
    print("--- NFTs currently in wallet ---")
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    url = f"https://deep-index.moralis.io/api/v2.2/{WALLET}/nft"
    resp = httpx.get(url, headers=headers, params={"chain": "eth"}, timeout=15)
    if resp.status_code == 200:
        nfts = resp.json().get("result", [])
        if nfts:
            for nft in nfts:
                name = nft.get("name", "?")
                tid = nft.get("token_id", "?")
                print(f"  Holding: {name} #{tid}")
        else:
            print("  No NFTs")


if __name__ == "__main__":
    main()
