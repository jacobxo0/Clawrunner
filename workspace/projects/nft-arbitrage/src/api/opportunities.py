"""
Opportunity endpoints — list, filter, approve/reject, manual execute.

Approve now triggers actual execution for the opportunity:
1. Sets status to 'approved'
2. Triggers the auto-executor to buy + sell
3. Records the trades
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from src.database import async_session
from src.models.opportunity import Opportunity
from src.schemas.opportunity import (
    OpportunityUpdate,
    OpportunityResponse,
    OpportunitySummary,
)

router = APIRouter(prefix="/api", tags=["opportunities"])


@router.get("/opportunities", response_model=list[OpportunitySummary])
async def list_opportunities(
    status: Optional[str] = Query(None, description="Filter by status"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List opportunities with optional filters."""
    async with async_session() as session:
        query = select(Opportunity).order_by(Opportunity.created_at.desc())

        if status:
            query = query.where(Opportunity.status == status)
        if strategy:
            query = query.where(Opportunity.strategy == strategy)

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        opportunities = result.scalars().all()
        return [OpportunitySummary.model_validate(o) for o in opportunities]


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: str):
    """Get a single opportunity by ID."""
    async with async_session() as session:
        result = await session.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return OpportunityResponse.model_validate(opportunity)


@router.patch("/opportunities/{opportunity_id}")
async def update_opportunity(opportunity_id: str, payload: OpportunityUpdate):
    """
    Update an opportunity status.

    - 'approved' → triggers execution (buy + sell)
    - 'rejected' → marks as rejected, no action
    """
    async with async_session() as session:
        result = await session.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        update_data = payload.model_dump(exclude_unset=True)

        if "status" in update_data:
            valid_statuses = {"pending", "approved", "rejected", "executed", "expired"}
            if update_data["status"] not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {valid_statuses}",
                )

        new_status = update_data.get("status", "")

        # If approving → trigger execution
        if new_status == "approved" and opportunity.status == "pending":
            try:
                from src.execution.auto_executor import AutoExecutor
                executor = AutoExecutor()

                opp_dict = {
                    "id": opportunity.id,
                    "strategy": opportunity.strategy,
                    "collection_id": opportunity.collection_id,
                    "token_id": opportunity.token_id,
                    "buy_venue": opportunity.buy_venue,
                    "sell_venue": opportunity.sell_venue,
                    "buy_price": float(opportunity.buy_price or 0),
                    "expected_exit": float(opportunity.expected_exit or 0),
                    "net_profit": float(opportunity.net_profit or 0),
                    "roi": float(opportunity.roi or 0),
                    "listing_order_hash": opportunity.listing_order_hash,
                    "bid_order_hash": opportunity.bid_order_hash,
                    "collection_slug": "",
                }

                exec_result = await executor.execute_opportunity(opp_dict)

                if exec_result["status"] == "executed":
                    opportunity.status = "executed"
                elif exec_result["status"] == "aborted":
                    opportunity.status = "approved"
                    # Still mark as approved even if bid expired
                else:
                    opportunity.status = "approved"

            except Exception as e:
                # If execution fails, still mark as approved
                opportunity.status = "approved"

        else:
            for field, value in update_data.items():
                setattr(opportunity, field, value)

        await session.commit()
        await session.refresh(opportunity)

        return {
            "id": opportunity.id,
            "status": opportunity.status,
            "strategy": opportunity.strategy,
            "token_id": opportunity.token_id,
            "buy_price": float(opportunity.buy_price or 0),
            "expected_exit": float(opportunity.expected_exit or 0),
            "net_profit": float(opportunity.net_profit or 0),
        }
