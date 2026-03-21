"""Verify executed trades on-chain"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://ethereum-rpc.publicnode.com'))

buy_tx = '0x843befdbe6eb248136b2ba163e9eebadc9befcb77e018ed6d9407e57c9f30221'
sell_tx = '0x456f20f8d0d554934dd29f3681a0cd43490f0ac92b4ed514679b49827b952083'

for label, tx_hash in [('BUY', buy_tx), ('SELL', sell_tx)]:
    print(f"\n--- {label} TX: {tx_hash} ---")
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        status_str = "SUCCESS" if receipt.status == 1 else "REVERTED"
        print(f"  Status: {status_str} (code={receipt.status})")
        print(f"  Block: {receipt.blockNumber}")
        print(f"  Gas used: {receipt.gasUsed}")
    except Exception as e:
        print(f"  Receipt NOT FOUND: {e}")

    try:
        tx = w3.eth.get_transaction(tx_hash)
        sender = tx["from"]
        to = tx["to"]
        value = Web3.from_wei(tx["value"], "ether")
        print(f"  From: {sender}")
        print(f"  To: {to}")
        print(f"  Value: {value} ETH")
        print(f"  Gas price: {Web3.from_wei(tx['gasPrice'], 'gwei')} gwei")
    except Exception as e:
        print(f"  TX details NOT FOUND: {e}")

# Also check wallet balance
wallet = w3.eth.account.from_key.__func__  # just checking balance
from dotenv import load_dotenv
import os
load_dotenv()
pk = os.getenv("WALLET_PRIVATE_KEY", "")
if pk:
    from eth_account import Account
    acct = Account.from_key(pk)
    bal = w3.eth.get_balance(acct.address)
    print(f"\nWallet {acct.address}: {Web3.from_wei(bal, 'ether')} ETH on Ethereum")
