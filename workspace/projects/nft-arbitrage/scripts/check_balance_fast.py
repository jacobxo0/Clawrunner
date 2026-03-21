"""Quick balance check + known transaction costs."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account
import os

load_dotenv()
pk = os.getenv("ETH_PRIVATE_KEY", "")
acct = Account.from_key(pk)
wallet = acct.address

w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))

print(f"Wallet: {wallet}")
print(f"Current ETH balance: {Web3.from_wei(w3.eth.get_balance(wallet), 'ether')} ETH")
print()

# Known transaction hashes from the database
known_txs = [
    ("BUY cryptocoven #6450", "0x843befdbe6eb248136b2ba163e9eebadc9befcb77e018ed6d9407e57c9f30221"),
    ("SELL cryptocoven #6450", "0x456f20f8d0d554934dd29f3681a0cd43490f0ac92b4ed514679b49827b952083"),
]

# Also check the failed tx that was "not confirmed" - 0x4dac60f0...
# Let's check the nonce to find ALL transactions
nonce = w3.eth.get_transaction_count(wallet)
print(f"Total transactions (nonce): {nonce}")
print()

total_gas_spent = 0
total_value_sent = 0

for label, tx_hash in known_txs:
    try:
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        gas_cost = float(Web3.from_wei(receipt["gasUsed"] * receipt["effectiveGasPrice"], "ether"))
        value = float(Web3.from_wei(tx["value"], "ether"))
        status = "SUCCESS" if receipt["status"] == 1 else "REVERTED"
        total_gas_spent += gas_cost
        total_value_sent += value
        
        print(f"{label}: {status}")
        print(f"  Value sent: {value:.6f} ETH")
        print(f"  Gas cost:   {gas_cost:.8f} ETH")
        print(f"  Nonce:      {tx['nonce']}")
        print()
    except Exception as e:
        print(f"{label}: ERROR - {e}")
        print()

# Check for any OTHER transactions by scanning nonces 0 to current
print("Scanning all nonces for unknown transactions...")
print()
for n in range(nonce):
    # We already know nonces from the known txs, skip those
    already_known = False
    for _, tx_hash in known_txs:
        try:
            tx = w3.eth.get_transaction(tx_hash)
            if tx["nonce"] == n:
                already_known = True
                break
        except:
            pass
    
    if already_known:
        continue
    
    # Find tx with this nonce by checking pending/recent
    # This is harder without an indexer, but let's try via block scan
    print(f"  Nonce {n}: (checking...)")

# Check if we received ETH from the sell (WETH vs ETH)
print()
print("=== SUMMARY ===")
print(f"Total value sent:  {total_value_sent:.6f} ETH")
print(f"Total gas spent:   {total_gas_spent:.8f} ETH")
print(f"Total outflow:     {total_value_sent + total_gas_spent:.6f} ETH")
print()
print("NOTE: The sell tx (accept bid) pays you in WETH, not ETH.")
print("Let's check WETH balance...")

# Check WETH balance
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
weth_abi = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
weth = w3.eth.contract(address=Web3.to_checksum_address(WETH), abi=weth_abi)
weth_balance = weth.functions.balanceOf(wallet).call()
print(f"WETH balance: {Web3.from_wei(weth_balance, 'ether')} WETH")
