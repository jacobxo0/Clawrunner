"""
Meta-Learning Agent — weekly AI-powered system optimization.

Uses Claude/GPT to analyze the full trading history and identify:
1. Which strategies are actually profitable (not just by numbers, but by pattern)
2. Which collections are consistently profitable vs risky
3. Parameter suggestions based on market regime
4. Emerging patterns the rule-based system might miss
5. Risk warnings from unusual market behavior

The AI sees the complete picture that individual components can't:
  - Strategy A works in bull markets but fails in bear
  - Collection X has good spreads but bids get cancelled before execution
  - Gas costs are eating too much profit on small trades
  - Cross-marketplace spreads dried up → adjust strategy weights

Output: Actionable recommendations that can be auto-applied or sent for review.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func, and_

from src.config import get_settings
from src.database import async_session
from src.models.opportunity import Opportunity
from src.models.trade import Trade
from src.models.collection import Collection

logger = logging.getLogger(__name__)


class MetaLearningAgent:
    """
    Weekly AI meta-analysis of system performance.
    Synthesizes trading data into actionable insights.
    """

    def __init__(self):
        settings = get_settings()
        self.ai_cfg = settings.self_improvement.get("meta_learning", {})
        self.provider = self.ai_cfg.get("ai_provider", "anthropic")
        self.auto_apply_threshold = self.ai_cfg.get(
            "auto_apply_confidence_threshold", 0.8
        )

    async def run_weekly_review(self) -> dict:
        """
        Run the complete weekly meta-learning review.

        Steps:
        1. Gather all data from the past week
        2. Build analysis prompt with rich context
        3. Send to AI for analysis
        4. Parse recommendations
        5. Auto-apply high-confidence changes (or send for review)
        """
        logger.info("meta_learning_starting_weekly_review")

        # Step 1: Gather data
        data = await self._gather_weekly_data()

        if not data.get("has_data"):
            logger.info("meta_learning_no_data_to_analyze")
            return {
                "status": "skipped",
                "reason": "Insufficient data for analysis",
            }

        # Step 2: Build prompt
        prompt = self._build_analysis_prompt(data)

        # Step 3: Send to AI
        ai_response = await self._query_ai(prompt)

        if not ai_response:
            logger.warning("meta_learning_ai_response_empty")
            return {"status": "error", "reason": "AI analysis returned empty"}

        # Step 4: Parse recommendations
        recommendations = self._parse_recommendations(ai_response)

        # Step 5: Notify
        await self._send_report(data, recommendations, ai_response)

        logger.info(
            "meta_learning_complete",
            recommendations=len(recommendations),
            auto_apply_eligible=sum(
                1 for r in recommendations
                if r.get("confidence", 0) >= self.auto_apply_threshold
            ),
        )

        return {
            "status": "success",
            "data_summary": data.get("summary", {}),
            "recommendations": recommendations,
            "raw_analysis": ai_response[:500],
        }

    async def _gather_weekly_data(self) -> dict:
        """Gather comprehensive trading data for the past week."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        try:
            async with async_session() as session:
                # Opportunities
                opp_result = await session.execute(
                    select(Opportunity).where(
                        Opportunity.created_at >= week_ago
                    )
                )
                opportunities = opp_result.scalars().all()

                # Trades
                trade_result = await session.execute(
                    select(Trade).where(
                        Trade.created_at >= week_ago
                    )
                )
                trades = trade_result.scalars().all()

                # Active collections
                col_result = await session.execute(
                    select(Collection).where(Collection.is_active == True)
                )
                collections = col_result.scalars().all()

        except Exception as e:
            logger.error("meta_learning_data_gather_error", error=str(e))
            return {"has_data": False}

        if not opportunities and not trades:
            return {"has_data": False}

        # Aggregate metrics
        total_opps = len(opportunities)
        approved_opps = sum(
            1 for o in opportunities if o.qc_verdict == "APPROVE"
        )
        rejected_opps = sum(
            1 for o in opportunities if o.qc_verdict == "REJECT"
        )
        executed_opps = sum(
            1 for o in opportunities if o.status == "executed"
        )

        # Strategy breakdown
        strategy_stats: dict[str, dict] = {}
        for opp in opportunities:
            strat = opp.strategy or "unknown"
            if strat not in strategy_stats:
                strategy_stats[strat] = {
                    "total": 0, "approved": 0, "executed": 0,
                    "avg_roi": [], "avg_profit": [],
                    "avg_confidence": [],
                }
            s = strategy_stats[strat]
            s["total"] += 1
            if opp.qc_verdict == "APPROVE":
                s["approved"] += 1
            if opp.status == "executed":
                s["executed"] += 1
            if opp.roi:
                s["avg_roi"].append(float(opp.roi))
            if opp.net_profit:
                s["avg_profit"].append(float(opp.net_profit))
            if opp.confidence:
                s["avg_confidence"].append(float(opp.confidence))

        # Compute averages
        for strat, s in strategy_stats.items():
            s["avg_roi"] = (
                round(sum(s["avg_roi"]) / len(s["avg_roi"]), 2)
                if s["avg_roi"] else 0
            )
            s["avg_profit"] = (
                round(sum(s["avg_profit"]) / len(s["avg_profit"]), 4)
                if s["avg_profit"] else 0
            )
            s["avg_confidence"] = (
                round(sum(s["avg_confidence"]) / len(s["avg_confidence"]), 3)
                if s["avg_confidence"] else 0
            )

        # Collection breakdown
        collection_stats: dict[str, dict] = {}
        col_names = {str(c.id): c.slug for c in collections}
        for opp in opportunities:
            col_id = str(opp.collection_id or "")
            slug = col_names.get(col_id, col_id[:8])
            if slug not in collection_stats:
                collection_stats[slug] = {
                    "opportunities": 0, "executed": 0,
                    "total_profit": 0.0,
                }
            cs = collection_stats[slug]
            cs["opportunities"] += 1
            if opp.status == "executed":
                cs["executed"] += 1
            if opp.net_profit:
                cs["total_profit"] += float(opp.net_profit)

        # Trade P&L
        total_trades = len(trades)
        buy_trades = [t for t in trades if t.side == "buy"]
        sell_trades = [t for t in trades if t.side == "sell"]
        total_buy_cost = sum(float(t.price or 0) for t in buy_trades)
        total_sell_revenue = sum(float(t.price or 0) for t in sell_trades)
        total_gas = sum(float(t.gas_used or 0) for t in trades)

        summary = {
            "period": f"{week_ago.date()} to {now.date()}",
            "total_opportunities": total_opps,
            "approved": approved_opps,
            "rejected": rejected_opps,
            "executed": executed_opps,
            "approval_rate": f"{approved_opps / max(total_opps, 1) * 100:.1f}%",
            "execution_rate": f"{executed_opps / max(approved_opps, 1) * 100:.1f}%",
            "total_trades": total_trades,
            "total_buy_cost_eth": round(total_buy_cost, 4),
            "total_sell_revenue_eth": round(total_sell_revenue, 4),
            "gross_pnl_eth": round(total_sell_revenue - total_buy_cost, 4),
            "total_gas_eth": round(total_gas, 4),
            "net_pnl_eth": round(
                total_sell_revenue - total_buy_cost - total_gas, 4
            ),
            "strategy_stats": strategy_stats,
            "collection_stats": collection_stats,
            "active_collections": len(collections),
        }

        return {
            "has_data": True,
            "summary": summary,
            "strategy_stats": strategy_stats,
            "collection_stats": collection_stats,
        }

    def _build_analysis_prompt(self, data: dict) -> str:
        """Build a detailed prompt for the AI to analyze."""
        summary = data.get("summary", {})
        strategy_stats = data.get("strategy_stats", {})
        collection_stats = data.get("collection_stats", {})

        strategy_text = ""
        for strat, stats in strategy_stats.items():
            strategy_text += (
                f"\n  - {strat}: {stats['total']} opportunities, "
                f"{stats['executed']} executed, "
                f"avg ROI: {stats['avg_roi']}%, "
                f"avg profit: {stats['avg_profit']} ETH, "
                f"avg confidence: {stats['avg_confidence']}"
            )

        collection_text = ""
        for slug, stats in collection_stats.items():
            collection_text += (
                f"\n  - {slug}: {stats['opportunities']} opps, "
                f"{stats['executed']} executed, "
                f"total profit: {stats['total_profit']:.4f} ETH"
            )

        settings = get_settings()
        current_config = {
            "strategies": settings.strategies,
            "risk": settings.risk,
            "execution": settings.execution,
        }

        prompt = f"""You are the meta-learning AI for an autonomous NFT arbitrage system.
Analyze the following weekly performance data and provide actionable recommendations.

## System Overview
This bot finds NFT arbitrage opportunities across OpenSea and Blur marketplaces.
Strategies: bid_spread (buy listing → sell into bid), cross_marketplace (buy on one marketplace, sell on another),
trait_mispricing (buy mispriced rare NFTs), stale_listing (buy forgotten cheap listings),
sweep_front_run (front-run sweep buyers).

## Weekly Performance Summary
Period: {summary.get('period', 'N/A')}
Total opportunities found: {summary.get('total_opportunities', 0)}
Approved: {summary.get('approved', 0)} ({summary.get('approval_rate', '0%')})
Executed: {summary.get('executed', 0)} ({summary.get('execution_rate', '0%')})
Total trades: {summary.get('total_trades', 0)}
Gross P&L: {summary.get('gross_pnl_eth', 0)} ETH
Gas costs: {summary.get('total_gas_eth', 0)} ETH
Net P&L: {summary.get('net_pnl_eth', 0)} ETH

## Strategy Performance
{strategy_text}

## Collection Performance
{collection_text}

## Current Configuration
{current_config}

## Your Task
Provide a structured analysis with:

1. **Performance Assessment**: Is the system profitable? What's working, what isn't?

2. **Strategy Recommendations**: Should any strategy be disabled/enabled?
   Should parameters be adjusted? (e.g., min_roi, min_profit thresholds)

3. **Collection Recommendations**: Should any collections be added/removed?
   Which are the best performers?

4. **Risk Assessment**: Are we taking too much or too little risk?
   Any concerning patterns?

5. **Specific Parameter Changes**: Give exact parameter changes with confidence
   scores (0-1). Format each as:
   PARAM_CHANGE: [config_path] [current_value] -> [new_value] (confidence: X.X)
   Example: PARAM_CHANGE: strategies.bid_spread.min_roi 3.0 -> 2.5 (confidence: 0.7)

6. **Market Regime**: What's the current NFT market like?
   Bull/bear/sideways? How should we adapt?

Be concise and actionable. Focus on what will increase profit with minimal added risk."""

        return prompt

    async def _query_ai(self, prompt: str) -> str:
        """Send analysis prompt to AI provider."""
        settings = get_settings()

        if self.provider == "anthropic" and settings.ai.anthropic_api_key:
            return await self._query_anthropic(prompt, settings.ai)
        elif settings.ai.openai_api_key:
            return await self._query_openai(prompt, settings.ai)
        else:
            logger.warning("meta_learning_no_ai_key_configured")
            return ""

    async def _query_anthropic(self, prompt: str, ai_cfg) -> str:
        """Query Anthropic Claude for analysis."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=ai_cfg.anthropic_api_key)
            response = await client.messages.create(
                model=ai_cfg.model_anthropic,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error("meta_learning_anthropic_error", error=str(e))
            return ""

    async def _query_openai(self, prompt: str, ai_cfg) -> str:
        """Query OpenAI GPT for analysis (fallback)."""
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=ai_cfg.openai_api_key)
            response = await client.chat.completions.create(
                model=ai_cfg.model_openai,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("meta_learning_openai_error", error=str(e))
            return ""

    def _parse_recommendations(self, ai_response: str) -> list[dict]:
        """Parse structured recommendations from AI response."""
        recommendations = []

        for line in ai_response.split("\n"):
            line = line.strip()
            if line.startswith("PARAM_CHANGE:"):
                try:
                    parts = line.replace("PARAM_CHANGE:", "").strip()
                    # Parse: config_path current -> new (confidence: X.X)
                    tokens = parts.split()
                    if len(tokens) >= 5 and "->" in tokens:
                        arrow_idx = tokens.index("->")
                        config_path = tokens[0]
                        current_val = tokens[arrow_idx - 1]
                        new_val = tokens[arrow_idx + 1]

                        confidence = 0.5
                        for t in tokens:
                            if t.startswith("(confidence:"):
                                try:
                                    confidence = float(
                                        t.replace("(confidence:", "")
                                        .replace(")", "")
                                    )
                                except ValueError:
                                    pass

                        recommendations.append({
                            "type": "parameter_change",
                            "config_path": config_path,
                            "current_value": current_val,
                            "recommended_value": new_val,
                            "confidence": confidence,
                            "auto_apply": confidence >= self.auto_apply_threshold,
                        })
                except Exception as e:
                    logger.debug("meta_learning_parse_error", line=line[:50], error=str(e))

        return recommendations

    async def _send_report(
        self, data: dict, recommendations: list[dict], ai_analysis: str,
    ):
        """Send the meta-learning report via Telegram."""
        try:
            from src.notifications.telegram import TelegramNotifier

            notifier = TelegramNotifier()
            summary = data.get("summary", {})

            msg = (
                "<b>Weekly Meta-Learning Report</b>\n"
                f"Period: {summary.get('period', 'N/A')}\n\n"
                f"Opportunities: {summary.get('total_opportunities', 0)}\n"
                f"Executed: {summary.get('executed', 0)}\n"
                f"Net P&L: <b>{summary.get('net_pnl_eth', 0)} ETH</b>\n"
                f"Gas costs: {summary.get('total_gas_eth', 0)} ETH\n\n"
            )

            if recommendations:
                msg += f"<b>{len(recommendations)} Recommendations:</b>\n"
                for r in recommendations[:5]:
                    emoji = "✅" if r.get("auto_apply") else "👀"
                    msg += (
                        f"  {emoji} {r['config_path']}: "
                        f"{r['current_value']} → {r['recommended_value']} "
                        f"(conf: {r['confidence']})\n"
                    )

            # Truncate AI analysis for Telegram
            analysis_short = ai_analysis[:800] if ai_analysis else "No AI analysis available"
            msg += f"\n<b>AI Analysis (excerpt):</b>\n<pre>{analysis_short}</pre>"

            await notifier.send_message(msg)

        except Exception as e:
            logger.warning("meta_learning_report_send_error", error=str(e))
