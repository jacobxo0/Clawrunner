"""Full database report for nft_arbitrage.db"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("nft_arbitrage.db")
conn.row_factory = sqlite3.Row

c = conn.cursor()

# List all tables with row counts
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]
print("=" * 60)
print("TABLES")
print("=" * 60)
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM [{t}]")
    count = c.fetchone()[0]
    print(f"  {t}: {count} rows")

# Collections
print("\n" + "=" * 60)
print("COLLECTIONS")
print("=" * 60)
c.execute("SELECT * FROM collections")
for r in c.fetchall():
    d = dict(r)
    for k, v in d.items():
        print(f"  {k}: {v}")
    print("  ---")

# Opportunities - recent
print("\n" + "=" * 60)
print("RECENT OPPORTUNITIES (last 30)")
print("=" * 60)
try:
    c.execute("PRAGMA table_info(opportunities)")
    cols = [r[1] for r in c.fetchall()]
    print(f"  Columns: {cols}")
    print()
    c.execute("SELECT * FROM opportunities ORDER BY created_at DESC LIMIT 30")
    rows = c.fetchall()
    if not rows:
        print("  (no opportunities)")
    for r in rows:
        d = dict(r)
        print(f"  ID={d.get('id')} slug={d.get('slug')} token={d.get('token_id')} "
              f"buy={d.get('buy_price')} sell={d.get('sell_price')} "
              f"profit={d.get('net_profit')} status={d.get('status')} "
              f"chain={d.get('chain')} created={d.get('created_at')}")
except Exception as e:
    print(f"  Error: {e}")

# Trades
print("\n" + "=" * 60)
print("TRADES (last 20)")
print("=" * 60)
try:
    c.execute("PRAGMA table_info(trades)")
    cols = [r[1] for r in c.fetchall()]
    print(f"  Columns: {cols}")
    c.execute("SELECT * FROM trades ORDER BY created_at DESC LIMIT 20")
    rows = c.fetchall()
    if not rows:
        print("  (no trades)")
    for r in rows:
        d = dict(r)
        print(f"  {d}")
except Exception as e:
    print(f"  Error: {e}")

# Opportunity stats
print("\n" + "=" * 60)
print("OPPORTUNITY STATS")
print("=" * 60)
try:
    c.execute("SELECT status, COUNT(*) as cnt FROM opportunities GROUP BY status")
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]}")
    
    c.execute("SELECT slug, COUNT(*) as cnt FROM opportunities GROUP BY slug ORDER BY cnt DESC")
    print("\n  By collection:")
    for r in c.fetchall():
        print(f"    {r[0]}: {r[1]}")
    
    c.execute("""SELECT slug, MIN(net_profit), MAX(net_profit), AVG(net_profit), COUNT(*) 
                 FROM opportunities 
                 WHERE net_profit > 0 
                 GROUP BY slug""")
    print("\n  Profitable opportunities by collection:")
    for r in c.fetchall():
        print(f"    {r[0]}: min={r[1]:.4f} max={r[2]:.4f} avg={r[3]:.4f} count={r[4]}")
except Exception as e:
    print(f"  Error: {e}")

# Today's activity
print("\n" + "=" * 60)
print("TODAY'S ACTIVITY")
print("=" * 60)
try:
    c.execute("""SELECT slug, COUNT(*) as cnt, MIN(created_at), MAX(created_at)
                 FROM opportunities 
                 WHERE created_at >= date('now', '-1 day')
                 GROUP BY slug ORDER BY cnt DESC""")
    rows = c.fetchall()
    if not rows:
        print("  (no activity in last 24h)")
    for r in rows:
        print(f"  {r[0]}: {r[1]} opps, from {r[2]} to {r[3]}")
except Exception as e:
    print(f"  Error: {e}")

# Check any other interesting tables
for table_name in tables:
    if table_name not in ['collections', 'opportunities', 'trades', 'alembic_version']:
        print(f"\n{'=' * 60}")
        print(f"TABLE: {table_name} (sample)")
        print("=" * 60)
        try:
            c.execute(f"PRAGMA table_info([{table_name}])")
            cols = [r[1] for r in c.fetchall()]
            print(f"  Columns: {cols}")
            c.execute(f"SELECT * FROM [{table_name}] ORDER BY rowid DESC LIMIT 5")
            rows = c.fetchall()
            if not rows:
                print("  (empty)")
            for r in rows:
                print(f"  {dict(r)}")
        except Exception as e:
            print(f"  Error: {e}")

conn.close()
