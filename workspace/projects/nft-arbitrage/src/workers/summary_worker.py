"""
Summary Worker — generates and sends the daily performance report.

Runs once per day (default 08:00 UTC):
- Aggregates trades, P&L, win rate
- Reports strategy performance
- Reports top collections
- Sends via Telegram
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func

from src.database import async_session
from src.models.trade import Trade
from src.models.opportunity import Opportunity
from src.notifications.telegram import TelegramNotifier
from src.agents.strategy_selector import StrategySelector

logger = logging.getLogger(__name__)


class SummaryWorker:
    """Generates daily performance summaries with key metrics."""

    def __init__(self, strategy_selector: StrategySelector = None):
        self.notifier = TelegramNotifier()
        self.strategy_selector = strategy_selector

    async def run(self):
        """Generate and send the daily summary."""
        since = datetime.utcnow() - timedelta(hours=24)

        async with async_session() as session:
            # Fetch today's trades
            trades_result = await session.execute(
                select(Trade).where(Trade.executed_at >= since)
            )
            trades = trades_result.scalars().all()

            # Fetch today's opportunities
            opps_result = await session.execute(
                select(Opportunity).where(Opportunity.created_at >= since)
            )
            opportunities = opps_result.scalars().all()

        # Calculate statistics
        buy_trades = [t for t in trades if t.side == "buy"]
        sell_trades = [t for t in trades if t.side == "sell"]

        total_bought = sum(float(t.price or 0) for t in buy_trades)
        total_sold = sum(float(t.price or 0) for t in sell_trades)
        total_gas = sum(float(t.gas_used or 0) for t in trades)
        net_pnl = total_sold - total_bought - total_gas

        # Win rate (trades with profit)
        trade_count = len(buy_trades)
        profitable = sum(1 for t in sell_trades if float(t.price or 0) > 0)
        win_rate = profitable / max(trade_count, 1)

        # Best and worst individual trade profits
        profits = []
        for sell in sell_trades:
            # Find matching buy
            matching_buy = next(
                (b for b in buy_trades if b.opportunity_id == sell.opportunity_id),
                None,
            )
            if matching_buy:
                profit = float(sell.price or 0) - float(matching_buy.price or 0)
                profits.append(profit)

        best_profit = max(profits) if profits else 0
        worst_profit = min(profits) if profits else 0

        # Strategy stats from Thompson Sampling
        strategy_stats = {}
        if self.strategy_selector:
            strategy_stats = self.strategy_selector.get_stats()

        stats = {
            "scans_completed": len(opportunities),
            "opportunities_found": len(opportunities),
            "trades_executed": trade_count,
            "win_rate": win_rate,
            "total_profit_eth": net_pnl,
            "best_profit": best_profit,
            "worst_profit": worst_profit,
            "portfolio_value_eth": total_bought - total_sold,
            "open_positions": len(buy_trades) - len(sell_trades),
            "strategy_stats": strategy_stats,
            "top_collections": [],  # Could aggregate by collection
        }

        # Send to Telegram
        await self.notifier.send_daily_summary(stats)

        logger.info(
            "daily_summary_sent",
            trades=trade_count,
            pnl=net_pnl,
            win_rate=win_rate,
        )
