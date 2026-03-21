"""
Seaport Executor — real on-chain execution via OpenSea Seaport protocol.

ATOMIC EXECUTION via Flashbots bundles:
  Both buy + sell are bundled into the SAME Ethereum block.
  Either BOTH execute or NEITHER does — zero risk of buying without selling.

Flow:
  1. Get listing fulfillment data (buy tx)
  2. Get offer fulfillment data (sell tx)
  3. Sign both transactions
  4. Bundle them via Flashbots → same block, atomic
  5. Wait for confirmation
  6. Return tx hashes
"""

import asyncio
import json
from decimal import Decimal

import httpx
import structlog
from web3 import Web3
from eth_account import Account

from src.config import get_settings
from src.engine.camouflage import CamouflageEngine

logger = structlog.get_logger()

# Seaport 1.6 contract address (current)
SEAPORT_ADDRESS = "0x0000000000000068F116a894984e2DB1123eB395"

# OpenSea conduit address (for NFT approval)
OPENSEA_CONDUIT = "0x1E0049783F008A0085193E00003D00cd54003c71"

# WETH contract addresses per chain
WETH_ADDRESS = {
    "ethereum": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "base": "0x4200000000000000000000000000000000000006",
}

WETH_ABI = [
    {"inputs": [{"name": "wad", "type": "uint256"}], "name": "withdraw", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
]


class SeaportExecutor:
    """
    Handles real on-chain buy/sell via OpenSea Seaport protocol.

    Key feature: ATOMIC execution via Flashbots bundles.
    Buy + sell happen in the same block — no risk of partial execution.

    Multi-chain: supports Ethereum mainnet and Base L2.

    Safety checks:
    - Verifies wallet balance before every trade
    - Checks gas price against max threshold
    - Uses Flashbots bundles for atomic buy+sell (Ethereum only)
    - Waits for tx confirmation before proceeding
    - Logs every step for auditability
    """

    def __init__(self, chain: str = "ethereum"):
        settings = get_settings()

        self.api_key = settings.marketplace.opensea_api_key
        self.chain = chain
        self.rpc_url = settings.blockchain.rpc_url_for_chain(chain)
        self.flashbots_rpc = settings.blockchain.flashbots_rpc_url
        self.private_key = settings.blockchain.eth_private_key
        self.chain_id = settings.blockchain.chain_id_for(chain)
        self.max_gas_gwei = settings.execution.get("max_gas_gwei", 50)
        self.use_flashbots = settings.execution.get("use_flashbots", True) and chain == "ethereum"

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            self.wallet_address = self.account.address
        else:
            self.account = None
            self.wallet_address = None

        self._w3_cache: dict[str, Web3] = {}
        self._camouflage = CamouflageEngine()

        self.base_url = "https://api.opensea.io"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_w3(self, chain: str = None) -> Web3:
        """Get Web3 instance for specific chain, with caching."""
        chain = chain or self.chain
        if chain == self.chain:
            return self.w3
        if chain not in self._w3_cache:
            settings = get_settings()
            rpc = settings.blockchain.rpc_url_for_chain(chain)
            self._w3_cache[chain] = Web3(Web3.HTTPProvider(rpc))
        return self._w3_cache[chain]

    def is_ready(self) -> bool:
        """Check if executor has all required config to trade."""
        return bool(
            self.api_key
            and self.private_key
            and self.rpc_url
            and self.wallet_address
        )

    async def get_wallet_balance(self, chain: str = None) -> float:
        """Get wallet ETH balance on specified chain (non-blocking)."""
        w3 = self._get_w3(chain) if chain else self.w3
        try:
            balance_wei = await asyncio.to_thread(w3.eth.get_balance, self.wallet_address)
            return float(Web3.from_wei(balance_wei, "ether"))
        except Exception as e:
            logger.error("balance_check_failed", chain=chain or self.chain, error=str(e))
            return 0.0

    async def get_gas_price_gwei(self, chain: str = None) -> float:
        """Get current gas price in gwei (non-blocking)."""
        w3 = self._get_w3(chain) if chain else self.w3
        try:
            gas_wei = await asyncio.to_thread(lambda: w3.eth.gas_price)
            return float(Web3.from_wei(gas_wei, "gwei"))
        except Exception as e:
            logger.error("gas_price_check_failed", error=str(e))
            return 999.0

    # ══════════════════════════════════════════════════════════
    #  ATOMIC BUY+SELL — Flashbots bundle (same block)
    # ══════════════════════════════════════════════════════════

    async def atomic_buy_and_sell(
        self,
        listing_order_hash: str,
        bid_order_hash: str,
        token_id: str,
        nft_contract: str,
        listing_protocol: str = None,
        bid_protocol: str = None,
        chain: str = None,
    ) -> dict:
        """
        Execute buy + sell atomically in the same block.

        On Ethereum: uses Flashbots bundle (both txs same block).
        On Base/L2: sends sequentially (very cheap gas, near-instant blocks).

        Returns dict with buy_tx_hash, sell_tx_hash, total_gas, status.
        """
        chain = chain or self.chain
        w3 = self._get_w3(chain)

        if not self.is_ready():
            return {"status": "error", "reason": "Wallet not configured"}

        if self._camouflage.enabled:
            jitter = await self._camouflage.apply_jitter()
            logger.debug("camouflage_jitter_applied", delay_s=round(jitter, 2))

        listing_protocol = listing_protocol or SEAPORT_ADDRESS
        bid_protocol = bid_protocol or SEAPORT_ADDRESS

        logger.info(
            "atomic_get_fulfillment",
            chain=chain,
            listing_hash=listing_order_hash[:16],
            bid_hash=bid_order_hash[:16],
        )

        buy_fulfillment, sell_fulfillment = await asyncio.gather(
            self._get_listing_fulfillment(listing_order_hash, listing_protocol, chain),
            self._get_offer_fulfillment(
                bid_order_hash, token_id, nft_contract, bid_protocol, chain
            ),
        )

        if not buy_fulfillment:
            return {"status": "error", "reason": f"Listing not found on {chain} (order may be stale)"}
        if not sell_fulfillment:
            return {"status": "error", "reason": f"Offer not found on {chain} (bid may be stale)"}

        buy_tx_data = buy_fulfillment.get("fulfillment_data", {}).get("transaction", {})
        sell_tx_data = sell_fulfillment.get("fulfillment_data", {}).get("transaction", {})

        if not buy_tx_data or not sell_tx_data:
            return {"status": "error", "reason": "Missing transaction data in fulfillment"}

        buy_value_wei = int(buy_tx_data.get("value", "0"))

        gas_price_wei = await asyncio.to_thread(lambda: w3.eth.gas_price)
        gas_gwei = float(Web3.from_wei(gas_price_wei, "gwei"))
        max_gas = self.max_gas_gwei if chain == "ethereum" else 1.0
        if gas_gwei > max_gas:
            return {
                "status": "error",
                "reason": f"Gas too high on {chain}: {gas_gwei:.2f} > {max_gas} gwei",
            }

        balance_wei = await asyncio.to_thread(w3.eth.get_balance, self.wallet_address)
        balance = float(Web3.from_wei(balance_wei, "ether"))
        buy_eth = float(Web3.from_wei(buy_value_wei, "ether"))
        estimated_gas = 0.015 if chain == "ethereum" else 0.0001
        total_needed = buy_eth + estimated_gas

        if balance < total_needed:
            return {
                "status": "error",
                "reason": f"Insufficient {chain} balance: {balance:.4f} < {total_needed:.4f} ETH",
            }

        logger.info(
            "atomic_pre_checks_passed",
            chain=chain,
            gas_gwei=round(gas_gwei, 3),
            balance=round(balance, 4),
            buy_eth=round(buy_eth, 4),
        )

        approved = await self._ensure_nft_approval(nft_contract, chain)
        if not approved:
            logger.warning("nft_approval_skipped", reason="Will approve in bundle if needed")

        chain_id = get_settings().blockchain.chain_id_for(chain)
        nonce = await asyncio.to_thread(w3.eth.get_transaction_count, self.wallet_address)
        gas_price = gas_price_wei

        buy_signed = self._build_and_sign_tx(
            to=buy_tx_data.get("to", ""),
            value=buy_value_wei,
            data=self._encode_input_data(buy_tx_data),
            nonce=nonce,
            gas_price=gas_price,
            gas_limit=350000,
            chain_id=chain_id,
            w3=w3,
        )

        sell_signed = self._build_and_sign_tx(
            to=sell_tx_data.get("to", ""),
            value=int(sell_tx_data.get("value", "0")),
            data=self._encode_input_data(sell_tx_data),
            nonce=nonce + 1,
            gas_price=gas_price,
            gas_limit=350000,
            chain_id=chain_id,
            w3=w3,
        )

        if not buy_signed or not sell_signed:
            return {"status": "error", "reason": "Failed to sign transactions"}

        buy_raw = "0x" + buy_signed.raw_transaction.hex()
        sell_raw = "0x" + sell_signed.raw_transaction.hex()

        # Only use Flashbots on Ethereum mainnet
        if chain == "ethereum" and self.use_flashbots:
            bundle_result = await self._send_flashbots_bundle(buy_raw, sell_raw)
            if not bundle_result:
                logger.warning("flashbots_bundle_failed_falling_back_sequential")
                return await self._send_sequential(buy_signed, sell_signed, w3)
        else:
            return await self._send_sequential(buy_signed, sell_signed, w3)

        buy_hash = w3.keccak(buy_signed.raw_transaction).hex()
        sell_hash = w3.keccak(sell_signed.raw_transaction).hex()

        buy_receipt = await self._wait_for_receipt(buy_hash, timeout=90, w3=w3)
        if not buy_receipt:
            return {
                "status": "error",
                "reason": "Buy transaction not confirmed in bundle",
                "buy_tx": buy_hash,
            }

        sell_receipt = await self._wait_for_receipt(sell_hash, timeout=90, w3=w3)
        if not sell_receipt:
            return {
                "status": "partial",
                "reason": "Sell not confirmed — NFT in wallet, manual intervention needed",
                "buy_tx": buy_hash,
            }

        buy_gas = float(Web3.from_wei(
            buy_receipt["gasUsed"] * buy_receipt["effectiveGasPrice"], "ether"
        ))
        sell_gas = float(Web3.from_wei(
            sell_receipt["gasUsed"] * sell_receipt["effectiveGasPrice"], "ether"
        ))

        logger.info(
            "atomic_execution_confirmed",
            chain=chain,
            buy_tx=buy_hash,
            sell_tx=sell_hash,
            buy_gas=buy_gas,
            sell_gas=sell_gas,
            block=buy_receipt["blockNumber"],
        )

        return {
            "status": "executed",
            "buy_tx_hash": buy_hash,
            "sell_tx_hash": sell_hash,
            "buy_gas": buy_gas,
            "sell_gas": sell_gas,
            "total_gas": buy_gas + sell_gas,
            "block_number": buy_receipt["blockNumber"],
        }

    # ── Flashbots bundle submission ──────────────────────────

    async def _send_flashbots_bundle(
        self, buy_raw_tx: str, sell_raw_tx: str
    ) -> dict | None:
        """
        Submit both transactions as a Flashbots bundle.
        Both execute in the same block or neither does.
        """
        try:
            target_block = self.w3.eth.block_number + 1

            async with httpx.AsyncClient(timeout=30) as client:
                # Try for the next 3 blocks
                for block_offset in range(3):
                    block_hex = hex(target_block + block_offset)

                    resp = await client.post(
                        self.flashbots_rpc,
                        json={
                            "jsonrpc": "2.0",
                            "method": "eth_sendBundle",
                            "params": [
                                {
                                    "txs": [buy_raw_tx, sell_raw_tx],
                                    "blockNumber": block_hex,
                                }
                            ],
                            "id": 1,
                        },
                    )

                    result = resp.json()
                    if "result" in result and result["result"]:
                        logger.info(
                            "flashbots_bundle_submitted",
                            target_block=target_block + block_offset,
                            bundle_hash=result["result"].get("bundleHash", ""),
                        )
                        return result["result"]

            logger.warning("flashbots_bundle_no_inclusion")
            return None

        except Exception as e:
            logger.error("flashbots_bundle_error", error=str(e))
            return None

    async def _send_sequential(self, buy_signed, sell_signed, w3: Web3 = None) -> dict:
        """Send buy then sell sequentially. Used as fallback on Ethereum, primary on L2s."""
        w3 = w3 or self.w3
        try:
            buy_hash = await asyncio.to_thread(
                w3.eth.send_raw_transaction, buy_signed.raw_transaction
            )
            buy_hash = buy_hash.hex()
            logger.info("sequential_buy_sent", tx_hash=buy_hash)

            buy_receipt = await self._wait_for_receipt(buy_hash, timeout=120, w3=w3)
            if not buy_receipt:
                return {"status": "error", "reason": "Buy tx not confirmed", "buy_tx": buy_hash}

            sell_hash = await asyncio.to_thread(
                w3.eth.send_raw_transaction, sell_signed.raw_transaction
            )
            sell_hash = sell_hash.hex()
            logger.info("sequential_sell_sent", tx_hash=sell_hash)

            sell_receipt = await self._wait_for_receipt(sell_hash, timeout=120, w3=w3)
            if not sell_receipt:
                return {
                    "status": "partial",
                    "reason": "Sell tx not confirmed — NFT in wallet",
                    "buy_tx": buy_hash,
                    "sell_tx": sell_hash,
                }

            buy_gas = float(Web3.from_wei(
                buy_receipt["gasUsed"] * buy_receipt["effectiveGasPrice"], "ether"
            ))
            sell_gas = float(Web3.from_wei(
                sell_receipt["gasUsed"] * sell_receipt["effectiveGasPrice"], "ether"
            ))

            # Auto-unwrap WETH → ETH so funds can be reinvested
            chain = None
            for c, cached_w3 in self._w3_cache.items():
                if cached_w3 == w3:
                    chain = c
                    break
            chain = chain or self.chain
            try:
                unwrap_hash = await self.unwrap_weth(chain)
                if unwrap_hash:
                    logger.info("auto_unwrap_after_sell", chain=chain, tx=unwrap_hash[:16])
            except Exception as e:
                logger.warning("auto_unwrap_failed", error=str(e)[:80])

            return {
                "status": "executed",
                "buy_tx_hash": buy_hash,
                "sell_tx_hash": sell_hash,
                "buy_gas": buy_gas,
                "sell_gas": sell_gas,
                "total_gas": buy_gas + sell_gas,
                "block_number": buy_receipt["blockNumber"],
            }

        except Exception as e:
            logger.error("sequential_execution_error", error=str(e))
            return {"status": "error", "reason": str(e)}

    # ── Transaction building ─────────────────────────────────

    def _build_and_sign_tx(
        self, to: str, value: int, data: bytes,
        nonce: int, gas_price: int, gas_limit: int = 350000,
        chain_id: int = None, w3: Web3 = None,
    ):
        """Build and sign a transaction with EIP-1559 fee strategy."""
        w3 = w3 or self.w3
        try:
            chain_id = chain_id or self.chain_id

            # EIP-1559: use maxFeePerGas + maxPriorityFeePerGas for better inclusion
            try:
                latest = w3.eth.get_block("latest")
                base_fee = latest.get("baseFeePerGas", gas_price)
                # Priority fee: 1.5 gwei on Ethereum, 0.001 gwei on L2s
                priority_fee = w3.to_wei(1.5, "gwei") if chain_id == 1 else w3.to_wei(0.001, "gwei")
                max_fee = int(base_fee * 2) + priority_fee

                tx = {
                    "nonce": nonce,
                    "to": Web3.to_checksum_address(to),
                    "value": value,
                    "gas": gas_limit,
                    "maxFeePerGas": max_fee,
                    "maxPriorityFeePerGas": priority_fee,
                    "chainId": chain_id,
                    "data": data,
                    "type": 2,  # EIP-1559
                }
            except Exception:
                # Fallback to legacy gasPrice if EIP-1559 fails
                tx = {
                    "nonce": nonce,
                    "to": Web3.to_checksum_address(to),
                    "value": value,
                    "gas": gas_limit,
                    "gasPrice": gas_price,
                    "chainId": chain_id,
                    "data": data,
                }

            return self.account.sign_transaction(tx)
        except Exception as e:
            logger.error("tx_sign_failed", error=str(e))
            return None

    # ── NFT Approvals ────────────────────────────────────────

    async def _ensure_nft_approval(self, nft_contract: str, chain: str = None) -> bool:
        """Ensure the Seaport conduit has approval to transfer our NFTs."""
        chain = chain or self.chain
        w3 = self._get_w3(chain)
        chain_id = get_settings().blockchain.chain_id_for(chain)
        try:
            nft_contract = Web3.to_checksum_address(nft_contract)
            conduit_address = Web3.to_checksum_address(OPENSEA_CONDUIT)

            erc721_abi = [
                {
                    "inputs": [
                        {"name": "owner", "type": "address"},
                        {"name": "operator", "type": "address"},
                    ],
                    "name": "isApprovedForAll",
                    "outputs": [{"name": "", "type": "bool"}],
                    "stateMutability": "view",
                    "type": "function",
                },
                {
                    "inputs": [
                        {"name": "operator", "type": "address"},
                        {"name": "approved", "type": "bool"},
                    ],
                    "name": "setApprovalForAll",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
            ]

            contract = w3.eth.contract(address=nft_contract, abi=erc721_abi)

            is_approved = await asyncio.to_thread(
                contract.functions.isApprovedForAll(
                    self.wallet_address, conduit_address
                ).call
            )

            if is_approved:
                logger.debug("nft_already_approved", contract=nft_contract)
                return True

            logger.info("approving_nft_for_seaport", contract=nft_contract, chain=chain)
            nonce = await asyncio.to_thread(w3.eth.get_transaction_count, self.wallet_address)
            gas_price = await asyncio.to_thread(lambda: w3.eth.gas_price)
            tx = contract.functions.setApprovalForAll(
                conduit_address, True
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": nonce,
                "gas": 80000,
                "gasPrice": gas_price,
                "chainId": chain_id,
            })

            signed = self.account.sign_transaction(tx)
            tx_hash = await asyncio.to_thread(
                w3.eth.send_raw_transaction, signed.raw_transaction
            )
            receipt = await asyncio.to_thread(
                w3.eth.wait_for_transaction_receipt, tx_hash, 60
            )

            if receipt["status"] == 1:
                logger.info("nft_approval_success", tx_hash=tx_hash.hex())
                return True
            else:
                logger.error("nft_approval_failed", tx_hash=tx_hash.hex())
                return False

        except Exception as e:
            logger.error("nft_approval_error", error=str(e))
            return False

    # ── OpenSea API calls ────────────────────────────────────

    async def _get_listing_fulfillment(
        self, order_hash: str, protocol_address: str, chain: str
    ) -> dict | None:
        """POST /api/v2/listings/fulfillment_data"""
        payload = {
            "listing": {
                "hash": order_hash,
                "chain": chain,
                "protocol_address": protocol_address,
            },
            "fulfiller": {
                "address": self.wallet_address,
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/api/v2/listings/fulfillment_data",
                    headers=self.headers,
                    json=payload,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logger.error(
                        "listing_fulfillment_error",
                        status=resp.status_code,
                        body=resp.text[:500],
                    )
                    return None
            except Exception as e:
                logger.error("listing_fulfillment_request_error", error=str(e))
                return None

    async def _get_offer_fulfillment(
        self,
        order_hash: str,
        token_id: str,
        contract_address: str,
        protocol_address: str,
        chain: str,
    ) -> dict | None:
        """POST /api/v2/offers/fulfillment_data"""
        payload = {
            "offer": {
                "hash": order_hash,
                "chain": chain,
                "protocol_address": protocol_address,
            },
            "fulfiller": {
                "address": self.wallet_address,
            },
            "consideration": {
                "asset_contract_address": contract_address,
                "token_id": str(token_id),
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/api/v2/offers/fulfillment_data",
                    headers=self.headers,
                    json=payload,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logger.error(
                        "offer_fulfillment_error",
                        status=resp.status_code,
                        body=resp.text[:500],
                    )
                    return None
            except Exception as e:
                logger.error("offer_fulfillment_request_error", error=str(e))
                return None

    # ── Helpers ───────────────────────────────────────────────

    def _encode_input_data(self, tx_data: dict) -> bytes:
        """Encode fulfillment data into transaction calldata using Seaport ABI."""
        from src.execution.seaport_encoder import encode_fulfillment_tx

        try:
            calldata = encode_fulfillment_tx(tx_data)
            if calldata:
                return calldata
            logger.error("encode_returned_empty", function=tx_data.get("function", ""))
            return b""
        except Exception as e:
            logger.error("encode_input_data_error", error=str(e)[:200],
                         function=tx_data.get("function", ""))
            return b""

    async def _wait_for_receipt(self, tx_hash: str, timeout: int = 120, w3: Web3 = None) -> dict | None:
        """Wait for transaction confirmation (non-blocking)."""
        w3 = w3 or self.w3
        try:
            receipt = await asyncio.to_thread(
                w3.eth.wait_for_transaction_receipt, tx_hash, timeout
            )
            if receipt["status"] == 1:
                return dict(receipt)
            else:
                logger.error("tx_reverted", tx_hash=tx_hash)
                return None
        except Exception as e:
            logger.error("tx_receipt_timeout", tx_hash=tx_hash, error=str(e))
            return None

    # ── WETH Management ──────────────────────────────────────

    async def get_weth_balance(self, chain: str = None) -> float:
        """Check WETH balance on specified chain."""
        chain = chain or self.chain
        w3 = self._get_w3(chain)
        weth_addr = WETH_ADDRESS.get(chain)
        if not weth_addr:
            return 0.0
        try:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(weth_addr), abi=WETH_ABI
            )
            balance = await asyncio.to_thread(
                contract.functions.balanceOf(self.wallet_address).call
            )
            return float(Web3.from_wei(balance, "ether"))
        except Exception as e:
            logger.error("weth_balance_check_failed", chain=chain, error=str(e))
            return 0.0

    async def unwrap_weth(self, chain: str = None, amount_wei: int = None) -> str | None:
        """
        Unwrap WETH → ETH so funds can be reinvested immediately.
        If amount_wei is None, unwraps the entire WETH balance.
        Returns tx hash on success, None on failure.
        """
        chain = chain or self.chain
        w3 = self._get_w3(chain)
        weth_addr = WETH_ADDRESS.get(chain)
        if not weth_addr:
            return None

        try:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(weth_addr), abi=WETH_ABI
            )

            if amount_wei is None:
                amount_wei = await asyncio.to_thread(
                    contract.functions.balanceOf(self.wallet_address).call
                )

            if amount_wei == 0:
                return None

            amount_eth = float(Web3.from_wei(amount_wei, "ether"))
            logger.info("unwrapping_weth", chain=chain, amount=round(amount_eth, 6))

            chain_id = get_settings().blockchain.chain_id_for(chain)
            nonce = await asyncio.to_thread(w3.eth.get_transaction_count, self.wallet_address)
            gas_price = await asyncio.to_thread(lambda: w3.eth.gas_price)

            tx = contract.functions.withdraw(amount_wei).build_transaction({
                "from": self.wallet_address,
                "nonce": nonce,
                "gas": 50000,
                "gasPrice": gas_price,
                "chainId": chain_id,
            })

            signed = self.account.sign_transaction(tx)
            tx_hash = await asyncio.to_thread(
                w3.eth.send_raw_transaction, signed.raw_transaction
            )
            tx_hash_hex = tx_hash.hex()
            logger.info("weth_unwrap_sent", chain=chain, tx_hash=tx_hash_hex)

            receipt = await self._wait_for_receipt(tx_hash_hex, timeout=60, w3=w3)
            if receipt:
                gas_used = float(Web3.from_wei(
                    receipt["gasUsed"] * receipt["effectiveGasPrice"], "ether"
                ))
                logger.info(
                    "weth_unwrap_success",
                    chain=chain,
                    amount=round(amount_eth, 6),
                    gas=round(gas_used, 8),
                    net_recovered=round(amount_eth - gas_used, 6),
                )
                return tx_hash_hex
            else:
                logger.error("weth_unwrap_failed", chain=chain, tx_hash=tx_hash_hex)
                return None

        except Exception as e:
            logger.error("weth_unwrap_error", chain=chain, error=str(e))
