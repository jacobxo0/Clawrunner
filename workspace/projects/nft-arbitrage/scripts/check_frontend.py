"""Check what the frontend sees."""
import requests

print("=== HEALTH ===")
h = requests.get("http://localhost:8000/health").json()
print(f"  Status: {h['status']}")
print(f"  Wallet: {h['wallet']['address']}")
print(f"  Balance: {h['wallet']['balance_eth']} ETH")
print(f"  Stream: connected={h['stream']['connected']}, events={h['stream']['events_received']}")

print("\n=== DASHBOARD STATS ===")
s = requests.get("http://localhost:8000/api/dashboard/stats").json()
print(f"  Collections: {s['total_collections']} ({s['active_collections']} active)")
print(f"  Opportunities found: {s['total_opportunities']}")
print(f"  Trades attempted: {s['total_trades']}")
print(f"  Profit so far: {s['total_profit_eth']} ETH")

print("\n=== TOP OPPORTUNITIES ===")
opps = requests.get("http://localhost:8000/api/opportunities?limit=5").json()
for o in opps[:5]:
    print(f"  {o.get('strategy','?'):15s} token={str(o.get('token_id','?')):6s} "
          f"profit={float(o.get('net_profit',0)):.4f} ETH  "
          f"roi={float(o.get('roi',0)):.1f}%  "
          f"status={o.get('status','?')}")

print("\n=== COLLECTIONS ===")
cols = requests.get("http://localhost:8000/api/collections").json()
for c in cols:
    floor = float(c.get("floor_price", 0) or 0)
    print(f"  {c['slug']:25s} floor={floor:.4f} ETH")

print("\n=== TRADES ===")
trades = requests.get("http://localhost:8000/api/trades").json()
print(f"  {len(trades)} trades recorded")
for t in trades[:5]:
    print(f"  {t.get('side','?'):5s} token={t.get('token_id','?')} "
          f"status={t.get('status','?')} tx={t.get('tx_hash','')[:20]}...")
