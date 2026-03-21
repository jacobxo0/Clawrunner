"""Check wallet balances and calculate trade profit"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account
import os

load_dotenv()
pk = os.getenv("ETH_PRIVATE_KEY", "")
acct = Account.from_key(pk)

w3_eth = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))
w3_base = Web3(Web3.HTTPProvider("https://base-rpc.publicnode.com"))

eth_bal = w3_eth.eth.get_balance(acct.address)
base_bal = w3_base.eth.get_balance(acct.address)

print(f"Wallet: {acct.address}")
print(f"Ethereum: {Web3.from_wei(eth_bal, 'ether')} ETH")
print(f"Base:     {Web3.from_wei(base_bal, 'ether')} ETH")
print()

buy_price = 0.00854
sell_price = 0.015
buy_gas = 145285 * 0.044526297e-9
sell_gas = 247616 * 0.044526297e-9
total_gas = buy_gas + sell_gas
gross_profit = sell_price - buy_price
net_profit = gross_profit - total_gas
print("=== CRYPTOCOVEN #6450 TRADE ===")
print(f"Buy:    {buy_price} ETH")
print(f"Sell:   {sell_price} ETH")
print(f"Gross:  {gross_profit:.6f} ETH")
print(f"Gas:    {total_gas:.8f} ETH")
print(f"Net:    {net_profit:.6f} ETH")
print(f"ROI:    {(net_profit / buy_price) * 100:.1f}%")
