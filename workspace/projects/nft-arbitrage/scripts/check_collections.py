"""Check which collections are seeded."""
import requests
r = requests.get("http://localhost:8000/api/collections")
cols = r.json()
print(f"{len(cols)} collections:")
for c in cols:
    slug = c.get("slug", "?")
    floor = c.get("floor_price", 0) or 0
    print(f"  {slug:25s} floor={float(floor):.4f} ETH")

print()
r2 = requests.get("http://localhost:8000/health")
h = r2.json()
w = h.get("wallet", {})
print(f"Wallet: {w.get('address','?')}")
print(f"Balance: {w.get('balance_eth',0)} ETH")
