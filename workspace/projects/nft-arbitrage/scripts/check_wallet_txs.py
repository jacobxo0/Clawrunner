"""Check all recent transactions from the wallet to find where ETH went."""
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

current_balance = w3.eth.get_balance(wallet)
print(f"Wallet: {wallet}")
print(f"Current balance: {Web3.from_wei(current_balance, 'ether')} ETH")
print()

# Check recent blocks for transactions from our wallet
latest_block = w3.eth.block_number
print(f"Latest block: {latest_block}")
print(f"Scanning last 500 blocks for outgoing transactions...")
print()

found_txs = []
for block_num in range(latest_block, latest_block - 500, -1):
    try:
        block = w3.eth.get_block(block_num, full_transactions=True)
        for tx in block.transactions:
            if tx["from"].lower() == wallet.lower():
                receipt = w3.eth.get_transaction_receipt(tx["hash"])
                gas_cost = receipt["gasUsed"] * receipt["effectiveGasPrice"]
                gas_eth = float(Web3.from_wei(gas_cost, "ether"))
                value_eth = float(Web3.from_wei(tx["value"], "ether"))
                status = "SUCCESS" if receipt["status"] == 1 else "REVERTED"
                
                found_txs.append({
                    "hash": tx["hash"].hex(),
                    "block": block_num,
                    "to": tx["to"],
                    "value": value_eth,
                    "gas_cost": gas_eth,
                    "total_spent": value_eth + gas_eth,
                    "status": status,
                    "method": tx["input"][:10].hex() if tx["input"] else "transfer",
                })
    except Exception:
        continue

if not found_txs:
    print("No outgoing transactions found in last 500 blocks")
else:
    print(f"Found {len(found_txs)} outgoing transactions:")
    print()
    total_spent = 0
    for tx in sorted(found_txs, key=lambda x: x["block"]):
        print(f"  Block {tx['block']} | {tx['status']}")
        print(f"    TX: 0x{tx['hash']}")
        print(f"    To: {tx['to']}")
        print(f"    Value: {tx['value']:.6f} ETH")
        print(f"    Gas:   {tx['gas_cost']:.6f} ETH")
        print(f"    Total: {tx['total_spent']:.6f} ETH")
        print()
        total_spent += tx["total_spent"]
    
    print(f"  TOTAL SPENT: {total_spent:.6f} ETH")
