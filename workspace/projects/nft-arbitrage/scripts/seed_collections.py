"""
Seed script — adds configured collections to the database
and fetches initial data from OpenSea.
"""

import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy import select

from src.config import get_settings
from src.database import async_session, init_db
from src.models.collection import Collection
from src.ingestion.opensea import OpenSeaClient
from src.ingestion.normalizer import EventNormalizer


async def main():
    print("Initializing database...")
    await init_db()

    settings = get_settings()
    opensea = OpenSeaClient()
    normalizer = EventNormalizer()

    print(f"Found {len(settings.collections)} collections in config\n")

    async with async_session() as session:
        for col_config in settings.collections:
            slug = col_config["slug"]

            # Check if exists
            existing = await session.execute(
                select(Collection).where(Collection.slug == slug)
            )
            if existing.scalar_one_or_none():
                print(f"  [{slug}] Already exists, skipping")
                continue

            # Fetch collection info from OpenSea
            print(f"  [{slug}] Fetching from OpenSea...")
            try:
                raw_stats = await opensea.get_collection_stats(slug)
                info = normalizer.normalize_collection_info(raw_stats)

                # Also get metadata for name/contracts
                raw_meta = await opensea.get_collection(slug)
                if raw_meta:
                    info["name"] = raw_meta.get("name", info.get("name", slug))
            except Exception as e:
                print(f"  [{slug}] Failed to fetch: {e}")
                info = {}

            collection = Collection(
                slug=slug,
                name=col_config.get("name", info.get("name", slug)),
                chain=col_config.get("chain", "ethereum"),
                contract_address=col_config.get("contract", ""),
                total_supply=info.get("total_supply"),
                royalty_bps=col_config.get("royalty_bps", 0),
                marketplace_fee_bps=col_config.get("marketplace_fee_bps", 250),
                floor_price=info.get("floor_price"),
                best_bid=info.get("best_bid"),
            )
            session.add(collection)
            print(f"  [{slug}] Added: floor={info.get('floor_price', 'N/A')} ETH")

        await session.commit()
        print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(main())
