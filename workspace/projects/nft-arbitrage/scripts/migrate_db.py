"""Add slug and chain columns to opportunities table."""
import sqlite3

conn = sqlite3.connect("nft_arbitrage.db")
c = conn.cursor()

c.execute("PRAGMA table_info(opportunities)")
cols = [r[1] for r in c.fetchall()]
print("Current columns:", cols)

if "slug" not in cols:
    c.execute("ALTER TABLE opportunities ADD COLUMN slug VARCHAR(255)")
    print("Added slug column")

if "chain" not in cols:
    c.execute("ALTER TABLE opportunities ADD COLUMN chain VARCHAR(50) DEFAULT 'ethereum'")
    print("Added chain column")

conn.commit()

c.execute("PRAGMA table_info(opportunities)")
cols = [r[1] for r in c.fetchall()]
print("Updated columns:", cols)

# Backfill slug from collection_id join
c.execute("""
    UPDATE opportunities 
    SET slug = (
        SELECT c.slug FROM collections c WHERE c.id = opportunities.collection_id
    ),
    chain = (
        SELECT c.chain FROM collections c WHERE c.id = opportunities.collection_id
    )
    WHERE slug IS NULL
""")
updated = c.rowcount
print(f"Backfilled {updated} rows with slug/chain from collections table")

conn.commit()
conn.close()
