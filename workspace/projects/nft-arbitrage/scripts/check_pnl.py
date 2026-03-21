"""Quick P&L check script."""
import sqlite3

conn = sqlite3.connect("nft_arbitrage.db")
cur = conn.cursor()

cur.execute(
    "SELECT opportunity_id, token_id, side, price, gas_used, status, executed_at "
    "FROM trades WHERE status = 'executed' ORDER BY executed_at"
)
trades = cur.fetchall()

buys = {}
results = []

for opp_id, token_id, side, price, gas, status, executed_at in trades:
    if side == "buy":
        buys[opp_id] = (token_id, price, gas, executed_at)
    elif side == "sell" and opp_id in buys:
        tid, buy_price, buy_gas, buy_time = buys[opp_id]
        gross = price - buy_price
        total_gas = buy_gas + gas
        net = gross - total_gas
        results.append((tid, buy_price, price, gross, total_gas, net, buy_time))

print("=" * 70)
print("EXECUTED ROUND-TRIP TRADES")
print("=" * 70)
for tid, bp, sp, gross, gas, net, when in results:
    print(f"  Token #{tid:>6s} | Buy {bp:.5f} -> Sell {sp:.5f} | "
          f"Gross {gross:.5f} | Gas {gas:.6f} | Net {net:.5f} ETH  [{when}]")

total_gross = sum(r[3] for r in results)
total_gas = sum(r[4] for r in results)
total_net = sum(r[5] for r in results)

print("=" * 70)
print(f"  Round-trips completed : {len(results)}")
print(f"  Total GROSS profit   : {total_gross:.5f} ETH")
print(f"  Total gas cost       : {total_gas:.6f} ETH")
print(f"  Total NET profit     : {total_net:.5f} ETH")
print(f"  Total NET profit USD : ~${total_net * 2700:.2f} (at ~$2700/ETH)")
print("=" * 70)

cur.execute("SELECT COUNT(*) FROM trades WHERE status = 'failed'")
failed = cur.fetchone()[0]
print(f"  Failed trades        : {failed}")

cur.execute("SELECT COUNT(*) FROM opportunities")
opps = cur.fetchone()[0]
print(f"  Opportunities found  : {opps}")

cur.execute("SELECT COUNT(*) FROM opportunities WHERE status = 'executed'")
executed = cur.fetchone()[0]
print(f"  Opportunities taken  : {executed}")
print(f"  Hit rate             : {executed/max(opps,1)*100:.2f}%")
print("=" * 70)

conn.close()
