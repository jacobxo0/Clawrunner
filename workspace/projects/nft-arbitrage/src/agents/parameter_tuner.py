"""
Parameter Tuner — auto-adjusts strategy parameters based on recent trade outcomes.

Runs daily. Analyzes the last N days of trades and opportunities to:
1. Tighten thresholds if hit rate is too low (too many failed trades)
2. Loosen thresholds if hit rate is too high (missing good opportunities)
3. Shift focus toward collections/strategies with best risk-adjusted returns
"""

import logging
from datetime import datetime, timedelta

import yaml
from sqlalchemy import select, func

from src.config import get_settings, CONFIG_DIR
from src.database import async_session
from src.models.trade import Trade
from src.models.opportunity import Opportunity
from src.notifications.telegram import TelegramNotifier

logger = logging.getLogger(__name__)


class ParameterTuner:
    """
    Adaptive parameter tuning based on observed trade performance.

    Uses a simple feedback loop:
    - If win rate < target: increase min thresholds (be more conservative)
    - If win rate > target: decrease min thresholds (capture more opportunities)
    - Always bounded by safe min/max ranges from strategies.yaml
    """

    def __init__(self):
        cfg = get_settings().self_improvement.get("parameter_tuner", {})
        self.lookback_days = cfg.get("lookback_days", 7)
        self.tighten_threshold = cfg.get("tighten_on_hit_rate_below", 0.5)
        self.loosen_threshold = cfg.get("loosen_on_hit_rate_above", 0.75)
        self.adjustment_step = 0.1  # 10% adjustment per tuning cycle
        self.notifier = TelegramNotifier()

    async def run(self):
        """Analyze recent performance and adjust parameters."""
        lookback = datetime.utcnow() - timedelta(days=self.lookback_days)

        async with async_session() as session:
            # Get recent trades
            trades_result = await session.execute(
                select(Trade).where(Trade.executed_at >= lookback)
            )
            trades = trades_result.scalars().all()

            # Get recent opportunities
            opps_result = await session.execute(
                select(Opportunity).where(Opportunity.created_at >= lookback)
            )
            opportunities = opps_result.scalars().all()

        if not trades:
            logger.info("No trades in lookback period, skipping tuning")
            return

        # Calculate performance metrics
        metrics = self._calculate_metrics(trades, opportunities)

        # Determine adjustments
        adjustments = self._determine_adjustments(metrics)

        # Apply adjustments (in-memory for now)
        if adjustments:
            await self._apply_adjustments(adjustments)
            await self._notify_adjustments(metrics, adjustments)

        logger.info(
            "parameter_tuning_complete",
            win_rate=metrics["win_rate"],
            avg_roi=metrics["avg_roi"],
            adjustments=len(adjustments),
        )

    def _calculate_metrics(self, trades: list, opportunities: list) -> dict:
        """Calculate performance metrics from recent data."""
        total_trades = len(trades)
        profitable_trades = sum(
            1 for t in trades if float(t.price or 0) > 0 and t.side == "sell"
        )
        win_rate = profitable_trades / max(total_trades, 1)

        # Calculate ROI metrics
        buy_trades = [t for t in trades if t.side == "buy"]
        sell_trades = [t for t in trades if t.side == "sell"]

        total_bought = sum(float(t.price or 0) for t in buy_trades)
        total_sold = sum(float(t.price or 0) for t in sell_trades)
        total_gas = sum(float(t.gas_used or 0) for t in trades)

        net_pnl = total_sold - total_bought - total_gas
        avg_roi = (net_pnl / max(total_bought, 0.001)) * 100

        # Opportunity conversion rate
        approved_opps = sum(
            1 for o in opportunities if o.qc_verdict == "APPROVE"
        )
        executed_opps = sum(
            1 for o in opportunities if o.status == "executed"
        )
        conversion_rate = executed_opps / max(approved_opps, 1)

        # Strategy breakdown
        strategy_performance = {}
        for trade in trades:
            # Group by strategy through opportunity
            strategy = getattr(trade, "strategy", "unknown")
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {"trades": 0, "profitable": 0}
            strategy_performance[strategy]["trades"] += 1
            if trade.side == "sell":
                strategy_performance[strategy]["profitable"] += 1

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_roi": avg_roi,
            "net_pnl": net_pnl,
            "total_bought": total_bought,
            "total_sold": total_sold,
            "conversion_rate": conversion_rate,
            "total_opportunities": len(opportunities),
            "strategy_performance": strategy_performance,
        }

    def _determine_adjustments(self, metrics: dict) -> list[dict]:
        """Determine what parameter adjustments to make."""
        adjustments = []

        win_rate = metrics["win_rate"]

        if win_rate < self.tighten_threshold:
            # Losing too often — be more conservative
            adjustments.append({
                "parameter": "min_roi_pct",
                "direction": "increase",
                "reason": f"Win rate {win_rate:.0%} below {self.tighten_threshold:.0%}",
                "factor": 1 + self.adjustment_step,
            })
            adjustments.append({
                "parameter": "auto_execute_confidence_min",
                "direction": "increase",
                "reason": f"Win rate low — require higher confidence",
                "factor": 1 + self.adjustment_step * 0.5,
            })
        elif win_rate > self.loosen_threshold:
            # Winning a lot — we might be too conservative, loosen up
            adjustments.append({
                "parameter": "min_roi_pct",
                "direction": "decrease",
                "reason": f"Win rate {win_rate:.0%} above {self.loosen_threshold:.0%}",
                "factor": 1 - self.adjustment_step * 0.5,
            })

        # If average ROI is negative, tighten significantly
        if metrics["avg_roi"] < 0:
            adjustments.append({
                "parameter": "min_profit_eth",
                "direction": "increase",
                "reason": f"Negative avg ROI ({metrics['avg_roi']:.1f}%)",
                "factor": 1 + self.adjustment_step * 2,
            })

        return adjustments

    async def _apply_adjustments(self, adjustments: list[dict]):
        """Apply parameter adjustments: persist to YAML and update in-memory settings."""
        strategies_path = CONFIG_DIR / "strategies.yaml"
        with open(strategies_path, "r", encoding="utf-8") as f:
            strategy_data = yaml.safe_load(f) or {}

        settings = get_settings()
        changes_made = []

        for adj in adjustments:
            param_name = adj["parameter"]
            factor = adj["factor"]

            # Search all strategies in strategies.yaml for the parameter
            for strat_name, strat_config in strategy_data.items():
                params = strat_config.get("parameters", {})
                if param_name in params:
                    p = params[param_name]
                    old_val = p.get("current", 0)
                    new_val = old_val * factor
                    # Clamp to min/max bounds
                    new_val = max(p.get("min", new_val), min(p.get("max", new_val), new_val))
                    new_val = round(new_val, 6)
                    p["current"] = new_val
                    changes_made.append(
                        f"{strat_name}.{param_name}: {old_val} -> {new_val}"
                    )
                    logger.info(
                        "parameter_persisted",
                        strategy=strat_name,
                        parameter=param_name,
                        old=old_val,
                        new=new_val,
                        reason=adj["reason"],
                    )

        # Write updated strategies.yaml
        if changes_made:
            with open(strategies_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(strategy_data, f, default_flow_style=False, sort_keys=False)

            # Update in-memory settings
            settings.yaml_strategies = strategy_data

            logger.info("parameters_persisted_to_yaml", changes=len(changes_made))

    async def _notify_adjustments(self, metrics: dict, adjustments: list[dict]):
        """Send Telegram notification about parameter changes."""
        text = (
            "<b>PARAMETER AUTO-TUNE</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Period: {self.lookback_days}d lookback\n"
            f"Win Rate: {metrics['win_rate']:.0%}\n"
            f"Avg ROI: {metrics['avg_roi']:.1f}%\n"
            f"Net P&L: {metrics['net_pnl']:.4f} ETH\n\n"
            "<b>Adjustments:</b>\n"
        )
        for adj in adjustments:
            text += f"  {adj['parameter']}: {adj['direction']} ({adj['reason']})\n"

        await self.notifier._send(text)
