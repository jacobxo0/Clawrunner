from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))
tx_hash = "0x4dac60f048fc8bbc9d5e2225322184653955074b079e933012a6383685499bc6"

try:
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    status_str = "SUCCESS" if receipt["status"] == 1 else "REVERTED"
    print(f"Status: {status_str} (code: {receipt['status']})")
    print(f"Block: {receipt['blockNumber']}")
    print(f"Gas used: {receipt['gasUsed']}")
    gas_cost = receipt["gasUsed"] * receipt["effectiveGasPrice"]
    print(f"Gas cost: {float(Web3.from_wei(gas_cost, 'ether')):.6f} ETH")
except Exception as e:
    print(f"Receipt error: {e}")

try:
    tx = w3.eth.get_transaction(tx_hash)
    print(f"Value: {float(Web3.from_wei(tx['value'], 'ether')):.6f} ETH")
    print(f"To: {tx['to']}")
    print(f"From: {tx['from']}")
    chain = tx.get("chainId", "unknown")
    print(f"Chain ID: {chain}")
except Exception as e:
    print(f"TX lookup error: {e}")

# Also check current balance
try:
    addr = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"
    bal = w3.eth.get_balance(addr)
    print(f"\nCurrent ETH balance: {float(Web3.from_wei(bal, 'ether')):.6f} ETH")
except Exception as e:
    print(f"Balance error: {e}")
