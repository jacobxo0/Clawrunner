"""Quick overnight status report from the database."""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("nft_arbitrage.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

# List tables + row counts
print("=" * 60)
print("DATABASE OVERVIEW")
print("=" * 60)
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM [{t}]")
    count = c.fetchone()[0]
    print(f"  {t}: {count} rows")

# Collections
print("\n" + "=" * 60)
print("ACTIVE COLLECTIONS")
print("=" * 60)
try:
    c.execute("SELECT slug, name, floor_price, best_bid, is_active, updated_at FROM collections ORDER BY floor_price ASC")
    for row in c.fetchall():
        slug, name, floor, bid, active, updated = row
        status = "ACTIVE" if active else "inactive"
        print(f"  [{status}] {slug}: floor={floor or '?'} ETH, best_bid={bid or '?'} ETH (updated: {updated or '?'})")
except Exception as e:
    print(f"  Error: {e}")

# Recent opportunities (last 24h)
print("\n" + "=" * 60)
print("OPPORTUNITIES (last 24h)")
print("=" * 60)
try:
    c.execute("""
        SELECT strategy, collection_id, token_id, buy_venue, sell_venue,
               buy_price, expected_exit, net_profit, roi, confidence,
               qc_verdict, status, created_at
        FROM opportunities
        ORDER BY created_at DESC
        LIMIT 50
    """)
    rows = c.fetchall()
    if rows:
        by_strategy = {}
        by_status = {}
        total_profit = 0
        for row in rows:
            strategy, col_id, token, bv, sv, buy, sell, profit, roi, conf, verdict, status, created = row
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            if profit:
                total_profit += float(profit)

        print(f"  Total: {len(rows)} opportunities")
        print(f"  By strategy: {dict(by_strategy)}")
        print(f"  By status: {dict(by_status)}")
        print(f"  Total potential profit: {total_profit:.6f} ETH")
        print()
        print("  Latest 10:")
        for row in rows[:10]:
            strategy, col_id, token, bv, sv, buy, sell, profit, roi, conf, verdict, status, created = row
            print(f"    [{status}] {strategy} | buy={buy} -> sell={sell} | profit={profit} ETH | ROI={roi}% | QC={verdict} | conf={conf} | {created}")
    else:
        print("  No opportunities found.")
except Exception as e:
    print(f"  Error: {e}")

# Trades
print("\n" + "=" * 60)
print("TRADES (all)")
print("=" * 60)
try:
    c.execute("""
        SELECT side, marketplace, price, gas_used, tx_hash, status, executed_at, created_at
        FROM trades
        ORDER BY created_at DESC
        LIMIT 20
    """)
    rows = c.fetchall()
    if rows:
        total_buys = sum(1 for r in rows if r[0] == "buy")
        total_sells = sum(1 for r in rows if r[0] == "sell")
        total_buy_eth = sum(float(r[2] or 0) for r in rows if r[0] == "buy")
        total_sell_eth = sum(float(r[2] or 0) for r in rows if r[0] == "sell")
        total_gas = sum(float(r[3] or 0) for r in rows)
        print(f"  Total trades: {len(rows)} (buys: {total_buys}, sells: {total_sells})")
        print(f"  Total bought: {total_buy_eth:.6f} ETH")
        print(f"  Total sold: {total_sell_eth:.6f} ETH")
        print(f"  Total gas: {total_gas:.6f} ETH")
        print(f"  Gross P&L: {total_sell_eth - total_buy_eth:.6f} ETH")
        print(f"  Net P&L: {total_sell_eth - total_buy_eth - total_gas:.6f} ETH")
        print()
        print("  Recent trades:")
        for row in rows[:10]:
            side, mp, price, gas, tx, status, executed, created = row
            print(f"    [{status}] {side} on {mp} | {price} ETH | gas={gas} | tx={tx and tx[:20] or '?'} | {executed or created}")
    else:
        print("  No trades executed yet.")
except Exception as e:
    print(f"  Error: {e}")

# Inventory
print("\n" + "=" * 60)
print("INVENTORY (currently held)")
print("=" * 60)
try:
    c.execute("""
        SELECT collection_id, token_id, acquisition_price, is_held, listed_price, acquired_at
        FROM inventory
        WHERE is_held = 1
        ORDER BY acquired_at DESC
    """)
    rows = c.fetchall()
    if rows:
        for row in rows:
            col, token, price, held, listed, acquired = row
            print(f"  Token #{token} | bought at {price} ETH | listed at {listed or 'not listed'} | acquired: {acquired}")
    else:
        print("  No NFTs currently held.")
except Exception as e:
    print(f"  Error: {e}")

# Agent decisions
print("\n" + "=" * 60)
print("AGENT DECISIONS (last 20)")
print("=" * 60)
try:
    c.execute("""
        SELECT agent_name, action, decision, confidence, reasoning, created_at
        FROM agents
        ORDER BY created_at DESC
        LIMIT 20
    """)
    rows = c.fetchall()
    if rows:
        for row in rows:
            agent, action, decision, conf, reasoning, created = row
            reason_short = (reasoning or "")[:80]
            print(f"  [{decision}] {agent} | {action} | conf={conf} | {reason_short} | {created}")
    else:
        print("  No agent decisions logged.")
except Exception as e:
    print(f"  Error: {e}")

# Market events summary
print("\n" + "=" * 60)
print("MARKET EVENTS (summary)")
print("=" * 60)
try:
    c.execute("SELECT event_type, COUNT(*) FROM market_events GROUP BY event_type")
    rows = c.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]} events")
    else:
        print("  No market events recorded.")
except Exception as e:
    print(f"  Error: {e}")

# Listings and bids counts
print("\n" + "=" * 60)
print("ACTIVE LISTINGS & BIDS")
print("=" * 60)
try:
    c.execute("SELECT COUNT(*) FROM listings WHERE is_active = 1")
    active_listings = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bids WHERE is_active = 1")
    active_bids = c.fetchone()[0]
    print(f"  Active listings: {active_listings}")
    print(f"  Active bids: {active_bids}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()
print("\n" + "=" * 60)
print("REPORT COMPLETE")
print("=" * 60)
