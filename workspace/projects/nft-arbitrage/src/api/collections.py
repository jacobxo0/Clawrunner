"""
Collection CRUD endpoints.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.database import async_session
from src.models.collection import Collection
from src.schemas.collection import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionSummary,
)

router = APIRouter(prefix="/api", tags=["collections"])


@router.get("/collections", response_model=list[CollectionSummary])
async def list_collections():
    """List all tracked collections."""
    async with async_session() as session:
        result = await session.execute(select(Collection).order_by(Collection.slug))
        collections = result.scalars().all()
        return [CollectionSummary.model_validate(c) for c in collections]


@router.get("/collections/{slug}", response_model=CollectionResponse)
async def get_collection(slug: str):
    """Get a single collection by slug."""
    async with async_session() as session:
        result = await session.execute(
            select(Collection).where(Collection.slug == slug)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        return CollectionResponse.model_validate(collection)


@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(payload: CollectionCreate):
    """Add a new collection to track."""
    async with async_session() as session:
        # Check for duplicate slug
        existing = await session.execute(
            select(Collection).where(Collection.slug == payload.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Collection slug already exists")

        collection = Collection(**payload.model_dump())
        session.add(collection)
        await session.commit()
        await session.refresh(collection)
        return CollectionResponse.model_validate(collection)


@router.patch("/collections/{slug}", response_model=CollectionResponse)
async def update_collection(slug: str, payload: CollectionUpdate):
    """Update a collection's fields."""
    async with async_session() as session:
        result = await session.execute(
            select(Collection).where(Collection.slug == slug)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(collection, field, value)

        await session.commit()
        await session.refresh(collection)
        return CollectionResponse.model_validate(collection)
