"""
Event Normalizer — transforms raw API data into normalized
database objects for consistent internal processing.

Supports:
  - OpenSea API v2 (listings, offers, events, stats)
  - Moralis API v2.2 (trades, transfers, owners)
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

import structlog

logger = structlog.get_logger()

WEI_PER_ETH = 10**18


class EventNormalizer:
    """
    Normalizes raw marketplace API responses into internal data structures.
    All marketplace-specific formats are converted to a unified schema.
    """

    # ═══════════════════════════════════════════════════════════
    # OpenSea Listings
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize_opensea_listing(raw: dict, collection_id: UUID) -> dict:
        price = _parse_opensea_price(raw)
        token_id = _extract_token_id(raw)
        maker = _extract_address(raw, "maker")

        return {
            "collection_id": collection_id,
            "token_id": str(token_id) if token_id else "",
            "marketplace": "opensea",
            "seller_address": maker,
            "price": Decimal(str(price)),
            "currency": _extract_currency(raw),
            "order_hash": raw.get("order_hash", ""),
            "protocol_address": raw.get("protocol_address", ""),
            "listed_at": _parse_timestamp(raw.get("created_date")),
            "expires_at": _parse_expiration(raw.get("expiration_time")),
            "traits": {},
        }

    # ═══════════════════════════════════════════════════════════
    # OpenSea Offers / Bids
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize_opensea_offer(raw: dict, collection_id: UUID) -> dict:
        price_obj = raw.get("price", {})
        price = _parse_offer_price(price_obj)

        criteria = raw.get("criteria", {})
        trait = criteria.get("trait")
        traits = criteria.get("traits", [])

        bid_type = "collection"
        trait_filter = {}
        token_id = None

        if trait:
            bid_type = "attribute"
            trait_filter = {"key": trait.get("type", ""), "value": trait.get("value", "")}
        elif traits:
            bid_type = "attribute"
            trait_filter = [{"key": t.get("type", ""), "value": t.get("value", "")} for t in traits]

        maker = ""
        protocol_data = raw.get("protocol_data", {})
        if protocol_data:
            params = protocol_data.get("parameters", {})
            maker = params.get("offerer", "")

        return {
            "collection_id": collection_id,
            "token_id": token_id,
            "marketplace": "opensea",
            "bidder_address": maker,
            "price": Decimal(str(price)),
            "currency": price_obj.get("currency", "WETH"),
            "expiry": None,
            "bid_type": bid_type,
            "trait_filter": trait_filter,
            "order_hash": raw.get("order_hash", ""),
            "protocol_address": raw.get("protocol_address", ""),
        }

    # ═══════════════════════════════════════════════════════════
    # OpenSea Sales (Events)
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize_opensea_sale(raw: dict, collection_id: UUID) -> dict:
        payment = raw.get("payment", {})
        price = _parse_payment_price(payment)

        nft = raw.get("nft", {})

        return {
            "event_type": "sale",
            "collection_id": collection_id,
            "token_id": str(nft.get("identifier", "")),
            "marketplace": "opensea",
            "price": Decimal(str(price)),
            "currency": payment.get("symbol", "ETH"),
            "from_address": raw.get("seller", ""),
            "to_address": raw.get("buyer", ""),
            "tx_hash": raw.get("transaction", ""),
            "event_timestamp": _parse_timestamp(raw.get("closing_date") or raw.get("event_timestamp")),
            "raw_data": raw,
        }

    # ═══════════════════════════════════════════════════════════
    # OpenSea Collection Stats
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize_opensea_stats(raw: dict) -> dict:
        total = raw.get("total", {})

        return {
            "floor_price": float(total.get("floor_price", 0) or 0),
            "volume_total": float(total.get("volume", 0) or 0),
            "sales_total": int(total.get("sales", 0) or 0),
            "average_price": float(total.get("average_price", 0) or 0),
            "owner_count": int(total.get("num_owners", 0) or 0),
            "market_cap": float(total.get("market_cap", 0) or 0),
        }

    # ═══════════════════════════════════════════════════════════
    # Moralis Trades
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize_moralis_trade(raw: dict, collection_id: UUID) -> dict:
        price_wei = raw.get("price", "0")
        try:
            price = int(price_wei) / WEI_PER_ETH
        except (ValueError, TypeError):
            price = 0.0

        token_ids = raw.get("token_ids", [])
        token_id = token_ids[0] if token_ids else ""

        return {
            "event_type": "sale",
            "collection_id": collection_id,
            "token_id": str(token_id),
            "marketplace": _identify_marketplace(raw.get("marketplace_address", "")),
            "price": Decimal(str(price)),
            "currency": "ETH",
            "from_address": raw.get("seller_address", ""),
            "to_address": raw.get("buyer_address", ""),
            "tx_hash": raw.get("transaction_hash", ""),
            "event_timestamp": _parse_timestamp(raw.get("block_timestamp")),
            "raw_data": raw,
        }

    # ═══════════════════════════════════════════════════════════
    # Moralis Transfers (for wash trade detection)
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize_moralis_transfer(raw: dict) -> dict:
        return {
            "from_address": raw.get("from_address", ""),
            "to_address": raw.get("to_address", ""),
            "token_id": raw.get("token_id", ""),
            "tx_hash": raw.get("transaction_hash", ""),
            "timestamp": _parse_timestamp(raw.get("block_timestamp")),
            "value": raw.get("value", "0"),
        }

    # ═══════════════════════════════════════════════════════════
    # Combined Collection Info (from OpenSea stats + metadata)
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize_collection_info(stats: dict, metadata: dict = None) -> dict:
        total = stats.get("total", {}) if "total" in stats else stats

        floor_price = float(total.get("floor_price", 0) or 0)
        volume_total = float(total.get("volume", 0) or total.get("volume_total", 0) or 0)
        owner_count = int(total.get("num_owners", 0) or total.get("owner_count", 0) or 0)

        result = {
            "floor_price": floor_price,
            "best_bid": 0,
            "royalty_bps": 0,
            "owner_count": owner_count,
            "volume_total": volume_total,
            "sales_total": int(total.get("sales", 0) or total.get("sales_total", 0) or 0),
            "average_price": float(total.get("average_price", 0) or 0),
            "market_cap": float(total.get("market_cap", 0) or 0),
        }

        if metadata:
            result["name"] = metadata.get("name", "")
            result["slug"] = metadata.get("collection", "")
            result["total_supply"] = int(metadata.get("total_supply", 0) or 0)

        return result


# ═══════════════════════════════════════════════════════════════
# Private helper functions
# ═══════════════════════════════════════════════════════════════

def _parse_opensea_price(raw: dict) -> float:
    price_obj = raw.get("price", {})
    if isinstance(price_obj, dict):
        current = price_obj.get("current", {})
        if current:
            try:
                value = int(current.get("value", "0"))
                decimals = int(current.get("decimals", 18))
                return value / (10**decimals)
            except (ValueError, TypeError):
                pass

    current_price = raw.get("current_price")
    if current_price:
        try:
            return int(current_price) / WEI_PER_ETH
        except (ValueError, TypeError):
            pass

    return 0.0


def _parse_offer_price(price_obj: dict) -> float:
    try:
        value = int(price_obj.get("value", "0"))
        decimals = int(price_obj.get("decimals", 18))
        return value / (10**decimals)
    except (ValueError, TypeError):
        return 0.0


def _parse_payment_price(payment: dict) -> float:
    try:
        quantity = int(payment.get("quantity", "0"))
        decimals = int(payment.get("decimals", 18))
        return quantity / (10**decimals)
    except (ValueError, TypeError):
        return 0.0


def _extract_token_id(raw: dict) -> str | None:
    bundle = raw.get("maker_asset_bundle", {})
    assets = bundle.get("assets", [])
    if assets:
        return assets[0].get("token_id")

    protocol = raw.get("protocol_data", {})
    params = protocol.get("parameters", {})
    offer_items = params.get("offer", [])
    if offer_items:
        return offer_items[0].get("identifierOrCriteria", "")

    return None


def _extract_address(raw: dict, field: str) -> str:
    value = raw.get(field, "")
    if isinstance(value, dict):
        return value.get("address", "")
    return str(value) if value else ""


def _extract_currency(raw: dict) -> str:
    price_obj = raw.get("price", {})
    if isinstance(price_obj, dict):
        current = price_obj.get("current", {})
        if current:
            return current.get("currency", "ETH")

    taker_bundle = raw.get("taker_asset_bundle", {})
    assets = taker_bundle.get("assets", [])
    if assets:
        contract = assets[0].get("asset_contract", {})
        schema = contract.get("schema_name", "")
        if schema == "ERC20":
            return "WETH"

    return "ETH"


def _parse_timestamp(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.utcfromtimestamp(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.utcfromtimestamp(int(value))
            except (ValueError, TypeError):
                return None
    return None


def _parse_expiration(value) -> datetime | None:
    if value is None:
        return None
    try:
        ts = int(value)
        if ts == 0:
            return None
        return datetime.utcfromtimestamp(ts)
    except (ValueError, TypeError):
        return _parse_timestamp(value)


_MARKETPLACE_CONTRACTS = {
    "0x00000000006c3852cbef3e08e8df289169ede581": "opensea_seaport",
    "0x00000000000001ad428e4906ae43d8f9852d0dd6": "opensea_seaport",
    "0x0000000000a39bb272e79075ade125fd351887ac": "blur",
    "0x39da41747a83aee658334415666f3ef92dd0d541": "blur",
    "0x59728544b08ab483533076417fbbb2fd0b17ce3a": "looksrare",
    "0x74312363e45dcaba76c59ec49a7aa8a65a67eed3": "x2y2",
}


def _identify_marketplace(contract_address: str) -> str:
    if not contract_address:
        return "unknown"
    return _MARKETPLACE_CONTRACTS.get(contract_address.lower(), "unknown")
