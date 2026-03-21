from web3 import Web3

ADDR = "0x3293eE612F280A49CC66AEB2fdd3EDAB5528cAC0"

for name, rpc in [("Ethereum", "https://ethereum-rpc.publicnode.com"),
                   ("Base", "https://base-rpc.publicnode.com")]:
    try:
        w3 = Web3(Web3.HTTPProvider(rpc))
        bal = w3.eth.get_balance(ADDR)
        eth = float(Web3.from_wei(bal, "ether"))
        gas = float(Web3.from_wei(w3.eth.gas_price, "gwei"))
        print(f"{name}: {eth:.6f} ETH | gas: {gas:.3f} gwei | connected: {w3.is_connected()}")
    except Exception as e:
        print(f"{name}: ERROR - {e}")
