"""
Redis Cache — fast access to best bids, floors, gas prices.
Falls back to in-memory dict if Redis is not available.
"""

import json
import time
from typing import Any

import structlog

from src.config import get_settings

logger = structlog.get_logger()


class RedisCache:
    """
    Cache for real-time market data.
    Uses Redis when available, falls back to in-memory dict.
    """

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._memory: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)
        self._use_memory = True
        settings = get_settings()
        self.default_ttl = settings.redis.ttl_seconds

    async def connect(self):
        """Try to connect to Redis. Fall back to memory if unavailable."""
        if self._use_memory and self._redis is None:
            try:
                import asyncio
                import redis.asyncio as aioredis
                settings = get_settings()
                self._redis = aioredis.from_url(
                    settings.redis.url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                await asyncio.wait_for(self._redis.ping(), timeout=3)
                self._use_memory = False
                logger.info("redis_connected")
            except BaseException:
                self._redis = None
                self._use_memory = True

    async def close(self):
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass

    async def get(self, key: str) -> Any:
        """Get a cached value."""
        if self._use_memory:
            return self._memory_get(key)
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            return self._memory_get(key)

    async def set(self, key: str, value: Any, ttl: int = None):
        """Set a cached value with TTL."""
        ttl = ttl or self.default_ttl

        # Always store in memory as fallback
        self._memory_set(key, value, ttl)

        if self._use_memory or not self._redis:
            return
        try:
            serialized = json.dumps(value, default=str)
            await self._redis.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))

    async def delete(self, key: str):
        """Delete a cached key."""
        self._memory.pop(key, None)
        if not self._use_memory and self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass

    # ── In-memory fallback ────────────────────────────────────

    def _memory_get(self, key: str) -> Any:
        entry = self._memory.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._memory[key]
            return None
        return value

    def _memory_set(self, key: str, value: Any, ttl: int):
        self._memory[key] = (value, time.time() + ttl)

    # ── Convenience methods ───────────────────────────────────

    async def set_floor_price(self, collection_id: str, price: float, ttl: int = 30):
        await self.set(f"floor:{collection_id}", {"price": price}, ttl=ttl)

    async def get_floor_price(self, collection_id: str) -> float:
        data = await self.get(f"floor:{collection_id}")
        return data["price"] if data else 0

    async def set_best_bid(self, collection_id: str, bid_data: dict, ttl: int = 30):
        await self.set(f"best_bid:{collection_id}", bid_data, ttl=ttl)

    async def get_best_bid(self, collection_id: str) -> dict | None:
        return await self.get(f"best_bid:{collection_id}")

    async def set_gas_price(self, gwei: float, ttl: int = 15):
        await self.set("eth:gas_price_gwei", {"gwei": gwei}, ttl=ttl)

    async def get_gas_price(self) -> float:
        data = await self.get("eth:gas_price_gwei")
        return data["gwei"] if data else 20.0

    async def set_trait_floors(self, collection_id: str, trait_data: dict, ttl: int = 300):
        await self.set(f"trait_floors:{collection_id}", trait_data, ttl=ttl)

    async def set_listing(self, collection_id: str, token_id: str, listing_data: dict, ttl: int = 60):
        await self.set(f"listing:{collection_id}:{token_id}", listing_data, ttl=ttl)
