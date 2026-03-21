"""
Discovery API — alpha signals, whale tracking, and collection discovery.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.get("/alpha")
async def get_alpha_signals():
    """Get current alpha signals — collections showing early growth signs."""
    from src.discovery.alpha_engine import AlphaEngine
    engine = AlphaEngine()
    try:
        results = await engine.discover()
        return {
            "status": "ok",
            "collections": results,
            "count": len(results),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "collections": []}


@router.get("/alpha/undervalued")
async def get_undervalued():
    """Get undervalued collections — high alpha score but low floor price."""
    from src.discovery.alpha_engine import AlphaEngine
    engine = AlphaEngine()
    try:
        results = await engine.find_undervalued(min_score=20)
        return {
            "status": "ok",
            "collections": results,
            "count": len(results),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "collections": []}


@router.get("/whales")
async def get_whale_activity():
    """Get recent whale wallet activity."""
    from src.discovery.whale_tracker import WhaleTracker
    tracker = WhaleTracker()
    try:
        results = await tracker.scan_whale_activity(hours=24)
        return {
            "status": "ok",
            "collections": results,
            "count": len(results),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "collections": []}


@router.get("/whales/hot")
async def get_whale_hot_collections():
    """Get collections where multiple whales are buying."""
    from src.discovery.whale_tracker import WhaleTracker
    tracker = WhaleTracker()
    try:
        results = await tracker.get_hot_collections(min_whales=2)
        return {
            "status": "ok",
            "collections": results,
            "count": len(results),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "collections": []}
