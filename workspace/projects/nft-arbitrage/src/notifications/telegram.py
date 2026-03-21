"""
Telegram Notifier — comprehensive trade and system notifications.

Sends:
- Trade execution alerts (every buy/sell)
- Opportunity alerts (high-confidence finds)
- System status (startup, errors, warnings)
- Daily performance summaries
- Trend shift alerts
- Risk warnings

Respects Telegram Bot API rate limits (429): retries once after Retry-After seconds.
"""

import asyncio
import logging
from datetime import datetime

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import RetryAfter

from src.config import get_settings

logger = logging.getLogger(__name__)


class TelegramNotifier:

    def __init__(self):
        settings = get_settings()
        self.bot_token = settings.telegram.bot_token
        self.chat_id = settings.telegram.chat_id
        self.enabled = settings.telegram.enabled and bool(self.bot_token) and bool(self.chat_id)

        notify_cfg = settings.notifications.get("telegram", {})
        self._notify_on_opportunity = notify_cfg.get("notify_on_opportunity", True)
        self._notify_on_trade = notify_cfg.get("notify_on_trade", True)
        self._notify_on_error = notify_cfg.get("notify_on_error", True)
        self._notify_on_summary = notify_cfg.get("notify_on_daily_summary", True)

        if self.enabled:
            self.bot = Bot(token=self.bot_token)
            logger.info("TelegramNotifier enabled — notifications will be sent")
        else:
            self.bot = None
            logger.warning("TelegramNotifier disabled (missing bot_token or chat_id)")

    async def _send(self, text: str) -> None:
        """Send a message to the configured Telegram chat. On 429 (rate limit), wait Retry-After and retry once."""
        if not self.enabled:
            logger.debug("Telegram disabled, skipping message")
            return
        for attempt in range(2):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
                return
            except RetryAfter as e:
                wait_s = getattr(e, "retry_after", 60) or 60
                logger.warning("Telegram rate limit (429), waiting %s s before retry", wait_s)
                await asyncio.sleep(wait_s)
            except Exception as exc:
                logger.error("Failed to send Telegram message: %s", exc)
                return
        logger.error("Failed to send Telegram message after rate-limit retry")

    # ── Trade notifications ────────────────────────────────────

    async def notify_trade_executed(
        self,
        opportunity: dict,
        buy_trade: dict,
        sell_trade: dict,
    ) -> None:
        """Notify when a full buy+sell trade cycle is executed."""
        if not self._notify_on_trade:
            return

        net_profit = float(opportunity.get("net_profit", 0))
        roi = float(opportunity.get("roi", 0))
        total_gas = float(buy_trade.get("gas_used", 0)) + float(sell_trade.get("gas_used", 0))

        text = (
            "<b>TRADE EXECUTED</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Strategy: <code>{opportunity.get('strategy', '?')}</code>\n"
            f"Collection: <code>{opportunity.get('collection_slug', opportunity.get('collection_id', '?'))}</code>\n"
            f"Token: <code>#{opportunity.get('token_id', '?')}</code>\n\n"
            f"BUY:  {buy_trade.get('price', 0):.4f} ETH @ {buy_trade.get('marketplace', '?')}\n"
            f"SELL: {sell_trade.get('price', 0):.4f} ETH @ {sell_trade.get('marketplace', '?')}\n\n"
            f"Net Profit: <b>{'+'if net_profit > 0 else ''}{net_profit:.4f} ETH</b>\n"
            f"ROI: <b>{roi:.1f}%</b>\n"
            f"Gas: ~{total_gas:.4f} ETH\n"
            f"Confidence: {opportunity.get('confidence', 0):.0%}\n"
            f"Status: <code>{buy_trade.get('status', '?')}</code>\n"
            f"Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}"
        )
        await self._send(text)

    async def notify_buy(self, trade: dict) -> None:
        """Notify on buy execution."""
        if not self._notify_on_trade:
            return

        text = (
            "<b>BUY ORDER</b>\n"
            f"Token: <code>#{trade.get('token_id', '?')}</code>\n"
            f"Price: {trade.get('price', 0):.4f} ETH\n"
            f"Market: {trade.get('marketplace', '?')}\n"
            f"Tx: <code>{trade.get('tx_hash', 'pending')}</code>"
        )
        await self._send(text)

    async def notify_sell(self, trade: dict) -> None:
        """Notify on sell execution (bid accepted)."""
        if not self._notify_on_trade:
            return

        text = (
            "<b>SELL ORDER (bid accepted)</b>\n"
            f"Token: <code>#{trade.get('token_id', '?')}</code>\n"
            f"Price: {trade.get('price', 0):.4f} ETH\n"
            f"Market: {trade.get('marketplace', '?')}\n"
            f"Tx: <code>{trade.get('tx_hash', 'pending')}</code>"
        )
        await self._send(text)

    async def notify_trade(self, trade: dict, side: str) -> None:
        """Legacy: Send a notification about a trade execution (buy or sell)."""
        if not self._notify_on_trade:
            return

        text = (
            f"<b>Trade {side.upper()}</b>\n"
            f"Token: <code>#{trade.get('token_id', '?')}</code>\n"
            f"Price: {trade.get('price', 0):.4f} ETH\n"
            f"Market: {trade.get('marketplace', '?')}\n"
            f"Tx: <code>{trade.get('tx_hash', 'N/A')}</code>"
        )
        await self._send(text)

    # ── Opportunity notifications ──────────────────────────────

    async def notify_opportunity(self, opp: dict) -> None:
        """Alert about a new high-confidence opportunity."""
        if not self._notify_on_opportunity:
            return

        text = (
            "<b>NEW OPPORTUNITY</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Strategy: <code>{opp.get('strategy', '?')}</code>\n"
            f"Collection: <code>{opp.get('collection_slug', opp.get('collection_id', '?'))}</code>\n"
            f"Token: <code>#{opp.get('token_id', '?')}</code>\n\n"
            f"Buy @ {opp.get('buy_price', 0):.4f} ETH ({opp.get('buy_venue', '?')})\n"
            f"Sell @ {opp.get('expected_exit', 0):.4f} ETH ({opp.get('sell_venue', '?')})\n\n"
            f"Net Profit: <b>{opp.get('net_profit', 0):.4f} ETH</b>\n"
            f"ROI: <b>{opp.get('roi', 0):.1f}%</b>\n"
            f"Confidence: {opp.get('confidence', 0):.0%}\n"
            f"QC: <code>{opp.get('qc_verdict', '?')}</code>"
        )
        await self._send(text)

    # ── System notifications ───────────────────────────────────

    async def notify_startup(self, mode: str, collections: int) -> None:
        """Notify that the system has started."""
        text = (
            "<b>SYSTEM STARTED</b>\n"
            f"Mode: <code>{mode}</code>\n"
            f"Collections: {collections}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        await self._send(text)

    async def notify_error(self, component: str, error: str) -> None:
        """Send critical error notification."""
        if not self._notify_on_error:
            return

        text = (
            "<b>SYSTEM ERROR</b>\n"
            f"Component: <code>{component}</code>\n"
            f"Error: {error[:500]}\n"
            f"Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}"
        )
        await self._send(text)

    async def notify_risk_warning(self, collection: str, reason: str) -> None:
        """Warn about risk threshold being exceeded."""
        text = (
            "<b>RISK WARNING</b>\n"
            f"Collection: <code>{collection}</code>\n"
            f"Reason: {reason}\n"
            f"Action: Auto-pausing trading for this collection"
        )
        await self._send(text)

    async def notify_trend_shift(self, collection: str, direction: str, score: float) -> None:
        """Alert when a significant trend shift is detected."""
        emoji_direction = "rising" if direction == "up" else "falling"
        text = (
            f"<b>TREND SHIFT ({emoji_direction})</b>\n"
            f"Collection: <code>{collection}</code>\n"
            f"Direction: {direction.upper()}\n"
            f"Trend Score: {score:.2f}\n"
            f"Time: {datetime.utcnow().strftime('%H:%M UTC')}"
        )
        await self._send(text)

    # ── Summary notifications ──────────────────────────────────

    async def send_daily_summary(self, stats: dict) -> None:
        """Send the daily performance summary."""
        if not self._notify_on_summary:
            return

        pnl = stats.get("total_profit_eth", 0)
        pnl_sign = "+" if pnl >= 0 else ""

        text = (
            "<b>DAILY SUMMARY</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Scans: {stats.get('scans_completed', 0)}\n"
            f"Opportunities: {stats.get('opportunities_found', 0)}\n"
            f"Trades: {stats.get('trades_executed', 0)}\n"
            f"Win Rate: {stats.get('win_rate', 0):.0%}\n\n"
            f"P&L: <b>{pnl_sign}{pnl:.4f} ETH</b>\n"
            f"Best trade: {stats.get('best_profit', 0):.4f} ETH\n"
            f"Worst trade: {stats.get('worst_profit', 0):.4f} ETH\n\n"
            f"Portfolio: {stats.get('portfolio_value_eth', 0):.4f} ETH\n"
            f"Open Positions: {stats.get('open_positions', 0)}\n\n"
            "<b>Strategy Performance:</b>\n"
        )

        strategy_stats = stats.get("strategy_stats", {})
        for name, s in strategy_stats.items():
            text += (
                f"  <code>{name}</code>: "
                f"{s.get('trades', 0)} trades, "
                f"{s.get('win_rate', 0):.0%} win, "
                f"E[success]={s.get('expected_success_rate', 0):.2f}\n"
            )

        text += f"\nTop Collections:\n"
        for col in stats.get("top_collections", [])[:3]:
            text += f"  {col.get('name', '?')}: {col.get('profit', 0):.4f} ETH\n"

        await self._send(text)
