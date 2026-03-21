import sqlite3
conn = sqlite3.connect("nft_arbitrage.db")
c = conn.cursor()
c.execute("SELECT slug, chain, contract_address, floor_price FROM collections")
for row in c.fetchall():
    contract = row[2][:20] if row[2] else "none"
    print(f"  {row[0]}: chain={row[1]} contract={contract}... floor={row[3]}")
conn.close()
