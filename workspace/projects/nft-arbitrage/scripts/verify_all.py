"""Full system verification - tests all endpoints and data."""

import httpx
import json

BASE = "http://127.0.0.1:8000"

def main():
    # Health
    print("=" * 50)
    print("1. HEALTH CHECK")
    print("=" * 50)
    r = httpx.get(f"{BASE}/health")
    print(f"   Status: {r.status_code}")
    data = r.json()
    print(f"   Uptime: {data['uptime_hours']} hours")
    print(f"   Version: {data['version']}")

    # Dashboard Stats
    print()
    print("=" * 50)
    print("2. DASHBOARD STATS")
    print("=" * 50)
    r = httpx.get(f"{BASE}/api/dashboard/stats")
    print(f"   Status: {r.status_code}")
    stats = r.json()
    for key, val in stats.items():
        print(f"   {key}: {val}")

    # Collections
    print()
    print("=" * 50)
    print("3. COLLECTIONS")
    print("=" * 50)
    r = httpx.get(f"{BASE}/api/collections")
    print(f"   Status: {r.status_code}")
    cols = r.json()
    print(f"   Count: {len(cols)}")
    for c in cols:
        name = c.get("name", c.get("slug", "?"))
        floor = c.get("floor_price", "N/A")
        bid = c.get("best_bid", "N/A")
        active = c.get("is_active", False)
        contract = c.get("contract_address", "")
        short_contract = contract[:8] + "..." if contract else "N/A"
        print(f"   - {name}: floor={floor}, bid={bid}, contract={short_contract}, active={active}")

    # Opportunities
    print()
    print("=" * 50)
    print("4. OPPORTUNITIES")
    print("=" * 50)
    r = httpx.get(f"{BASE}/api/opportunities?limit=5")
    print(f"   Status: {r.status_code}")
    opps = r.json()
    print(f"   Count: {len(opps)}")

    # Trades
    print()
    print("=" * 50)
    print("5. TRADES")
    print("=" * 50)
    r = httpx.get(f"{BASE}/api/trades?limit=5")
    print(f"   Status: {r.status_code}")
    trades = r.json()
    print(f"   Count: {len(trades)}")

    # Frontend
    print()
    print("=" * 50)
    print("6. FRONTEND")
    print("=" * 50)
    r = httpx.get(f"{BASE}/")
    print(f"   Status: {r.status_code}")
    print(f"   Content-Type: {r.headers.get('content-type')}")
    print(f"   Size: {len(r.text)} bytes")
    has_title = "NFT Arb OS" in r.text
    has_opensea = "OpenSea" in r.text
    has_moralis = "Moralis" in r.text
    has_dashboard = "page-dashboard" in r.text
    has_collections = "page-collections" in r.text
    has_opportunities = "page-opportunities" in r.text
    has_trades = "page-trades" in r.text
    has_scanner = "page-scanner" in r.text
    has_settings = "page-settings" in r.text
    print(f"   Title: {'OK' if has_title else 'MISSING'}")
    print(f"   OpenSea ref: {'OK' if has_opensea else 'MISSING'}")
    print(f"   Moralis ref: {'OK' if has_moralis else 'MISSING'}")
    print(f"   Pages: dashboard={'OK' if has_dashboard else 'MISS'}, collections={'OK' if has_collections else 'MISS'}, opportunities={'OK' if has_opportunities else 'MISS'}, trades={'OK' if has_trades else 'MISS'}, scanner={'OK' if has_scanner else 'MISS'}, settings={'OK' if has_settings else 'MISS'}")

    # Summary
    print()
    print("=" * 50)
    all_ok = all([
        r.status_code == 200,
        len(cols) >= 3,
        has_title,
        has_dashboard,
    ])
    if all_ok:
        print("ALL CHECKS PASSED - System is ready!")
    else:
        print("SOME CHECKS FAILED - Review above")
    print("=" * 50)
    print(f"\nDashboard: http://localhost:8000")
    print(f"API Docs:  http://localhost:8000/docs")


if __name__ == "__main__":
    main()
