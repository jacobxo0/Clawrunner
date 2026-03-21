"""Diagnose the bid price issue: what does OpenSea ACTUALLY return for offers?"""
import httpx
import json

API_KEY = "e73089173e1e45c4b016310dd9996677"
HEADERS = {"accept": "application/json", "x-api-key": API_KEY}
BASE = "https://api.opensea.io/api/v2"

SLUGS = ["cryptocoven", "tubby-cats", "beanzofficial", "thememes6529"]


def check_offers(slug):
    print(f"\n{'='*70}")
    print(f"OFFERS FOR: {slug}")
    print(f"{'='*70}")

    resp = httpx.get(
        f"{BASE}/offers/collection/{slug}",
        headers=HEADERS,
        params={"limit": 5},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"  Error: {resp.status_code}")
        return

    data = resp.json()
    offers = data.get("offers", [])

    stats = httpx.get(f"{BASE}/collections/{slug}/stats", headers=HEADERS, timeout=10)
    floor = 0
    if stats.status_code == 200:
        floor = float(stats.json().get("total", {}).get("floor_price", 0) or 0)
    print(f"  Floor price: {floor:.5f} ETH")

    for i, offer in enumerate(offers[:5]):
        price_obj = offer.get("price", {})
        value = int(price_obj.get("value", "0"))
        decimals = int(price_obj.get("decimals", 18))
        currency = price_obj.get("currency", "?")
        raw_price = value / (10 ** decimals)

        protocol = offer.get("protocol_data", {})
        params = protocol.get("parameters", {})
        offer_items = params.get("offer", [])
        consideration = params.get("consideration", [])

        # Check quantity in protocol data
        quantity = 1
        per_unit_amount = raw_price
        if offer_items:
            start_amount = int(offer_items[0].get("startAmount", "0"))
            item_type = offer_items[0].get("itemType", 0)
            if start_amount > 0 and decimals > 0:
                per_unit_amount = start_amount / (10 ** decimals)

        # Check consideration items (what the offerer wants back)
        nft_count = 0
        for c in consideration:
            if c.get("itemType") in [2, 3]:  # ERC721 or ERC1155
                nft_count += int(c.get("startAmount", 1))

        if nft_count > 1:
            per_unit_amount = raw_price / nft_count

        # What does the SELLER actually receive?
        seller_consideration = []
        for c in consideration:
            if c.get("itemType") in [2, 3]:
                continue  # NFT going to buyer
            recipient = c.get("recipient", "").lower()
            amount = int(c.get("startAmount", "0")) / (10 ** decimals)
            seller_consideration.append({
                "recipient": recipient[:16],
                "amount": amount,
            })

        print(f"\n  Offer #{i+1}:")
        print(f"    API price.value:     {raw_price:.6f} {currency}")
        print(f"    offer[0] startAmount: {per_unit_amount:.6f}")
        print(f"    NFTs requested:      {nft_count}")
        if nft_count > 1:
            print(f"    PER-UNIT price:      {raw_price / nft_count:.6f} *** MULTI-ITEM BID ***")
        print(f"    Consideration breakdown:")
        for sc in seller_consideration:
            print(f"      {sc['recipient']}.. -> {sc['amount']:.6f} WETH")

        # What the system THINKS vs reality
        system_sees = raw_price
        real_per_unit = raw_price / max(nft_count, 1)
        fees_pct = 0.075  # 7.5% typical
        seller_net = real_per_unit * (1 - fees_pct)

        print(f"    ---")
        print(f"    System thinks bid = {system_sees:.6f} ETH")
        print(f"    Real per-unit bid  = {real_per_unit:.6f} ETH")
        print(f"    Seller receives    ~ {seller_net:.6f} ETH (after 7.5% fees)")
        print(f"    Floor price        = {floor:.6f} ETH")
        if seller_net > floor:
            print(f"    PROFITABLE? YES  (net {seller_net - floor:.6f} ETH before gas)")
        else:
            print(f"    PROFITABLE? NO   (loss of {floor - seller_net:.6f} ETH)")


def main():
    for slug in SLUGS:
        check_offers(slug)


if __name__ == "__main__":
    main()
