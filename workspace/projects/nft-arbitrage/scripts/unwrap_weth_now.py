"""Unwrap all WETH to ETH right now."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def main():
    from src.execution.seaport import SeaportExecutor

    for chain in ("ethereum", "base"):
        print(f"\n=== {chain.upper()} ===")
        ex = SeaportExecutor(chain=chain)
        if not ex.is_ready():
            print("  Wallet not configured")
            continue

        eth_bal = await ex.get_wallet_balance(chain)
        weth_bal = await ex.get_weth_balance(chain)
        print(f"  ETH:  {eth_bal:.6f}")
        print(f"  WETH: {weth_bal:.6f}")
        print(f"  Total: {eth_bal + weth_bal:.6f}")

        if weth_bal > 0.0001:
            print(f"\n  Unwrapping {weth_bal:.6f} WETH -> ETH...")
            tx = await ex.unwrap_weth(chain)
            if tx:
                print(f"  SUCCESS! TX: {tx}")
                new_eth = await ex.get_wallet_balance(chain)
                new_weth = await ex.get_weth_balance(chain)
                print(f"  New ETH:  {new_eth:.6f}")
                print(f"  New WETH: {new_weth:.6f}")
            else:
                print("  FAILED to unwrap")
        else:
            print("  No WETH to unwrap")

asyncio.run(main())
