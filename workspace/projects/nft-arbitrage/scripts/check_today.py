import sqlite3
conn = sqlite3.connect("nft_arbitrage.db")
c = conn.cursor()

c.execute("""
    SELECT strategy, status, qc_verdict, COUNT(*) as cnt,
           AVG(net_profit) as avg_profit, AVG(roi) as avg_roi,
           MIN(created_at) as first_t, MAX(created_at) as last_t
    FROM opportunities
    WHERE created_at >= '2026-02-18'
    GROUP BY strategy, status, qc_verdict
    ORDER BY cnt DESC
""")
print("=== TODAY OPPORTUNITIES ===")
rows = c.fetchall()
if rows:
    for row in rows:
        print(f"  {row[0]} | {row[1]} | QC={row[2]} | count={row[3]} | avg_profit={row[4]:.6f} | avg_roi={row[5]:.2f}% | {row[6]} to {row[7]}")
else:
    print("  NONE - no opportunities found today!")

c.execute("""
    SELECT side, status, COUNT(*), marketplace,
           MIN(created_at), MAX(created_at)
    FROM trades WHERE created_at >= '2026-02-18'
    GROUP BY side, status, marketplace
""")
print("\n=== TODAY TRADES ===")
rows = c.fetchall()
if rows:
    for r in rows:
        print(f"  {r[0]} | {r[1]} | count={r[2]} | {r[3]} | {r[4]} to {r[5]}")
else:
    print("  NONE - no trades attempted today!")

c.execute("SELECT COUNT(*) FROM opportunities WHERE created_at >= '2026-02-18'")
t_opps = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM trades WHERE created_at >= '2026-02-18'")
t_trades = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM opportunities")
a_opps = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM trades")
a_trades = c.fetchone()[0]
print(f"\nToday: {t_opps} opps, {t_trades} trades")
print(f"All time: {a_opps} opps, {a_trades} trades")

c.execute("SELECT slug, floor_price, best_bid, updated_at FROM collections ORDER BY updated_at DESC")
print("\n=== COLLECTION LAST UPDATES ===")
for row in c.fetchall():
    print(f"  {row[0]}: floor={row[1]} bid={row[2]} updated={row[3]}")

# Check the latest opportunities overall
c.execute("""
    SELECT strategy, collection_id, buy_price, expected_exit, net_profit,
           roi, confidence, qc_verdict, status, created_at
    FROM opportunities ORDER BY created_at DESC LIMIT 5
""")
print("\n=== LAST 5 OPPORTUNITIES (any date) ===")
for row in c.fetchall():
    print(f"  {row[0]} | buy={row[2]} sell={row[3]} profit={row[4]} roi={row[5]}% | QC={row[7]} {row[8]} | {row[9]}")

# Check latest trades
c.execute("SELECT side, status, price, tx_hash, executed_at FROM trades ORDER BY created_at DESC LIMIT 5")
print("\n=== LAST 5 TRADES (any date) ===")
for row in c.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} ETH | tx={row[3][:20] if row[3] else 'none'} | {row[4]}")

conn.close()
