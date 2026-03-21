"""Check actual on-chain wallet state — where did the money go?"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from web3 import Web3

ETH_RPC = os.getenv("ETH_RPC_URL", "https://ethereum-rpc.publicnode.com")
PRIVATE_KEY = os.getenv("ETH_PRIVATE_KEY", "")
WETH_CONTRACT = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
WETH_ABI = [{"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}]


def main():
    w3 = Web3(Web3.HTTPProvider(ETH_RPC))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    addr = account.address

    eth_bal = w3.eth.get_balance(addr)
    eth_val = w3.from_wei(eth_bal, "ether")

    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_CONTRACT), abi=WETH_ABI)
    weth_bal = weth.functions.balanceOf(Web3.to_checksum_address(addr)).call()
    weth_val = w3.from_wei(weth_bal, "ether")

    total = float(eth_val) + float(weth_val)

    print(f"Wallet: {addr}")
    print(f"ETH:    {float(eth_val):.6f} ETH")
    print(f"WETH:   {float(weth_val):.6f} WETH")
    print(f"Total:  {total:.6f} ETH")
    print(f"Total:  ~${total * 1980:.2f} (at ~$1980/ETH)")

    nonce = w3.eth.get_transaction_count(addr)
    print(f"\nTotal transactions from wallet: {nonce}")

    print("\nChecking recent transactions...")
    block = w3.eth.block_number
    print(f"Current block: {block}")


if __name__ == "__main__":
    main()
