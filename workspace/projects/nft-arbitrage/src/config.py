"""
Configuration loader: merges YAML settings with environment variables.
Environment variables always take precedence over YAML values.
"""

import os
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_yaml(filename: str) -> dict:
    path = CONFIG_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class DatabaseSettings(BaseSettings):
    url: str = Field(default="sqlite+aiosqlite:///nft_arbitrage.db", alias="DATABASE_URL")
    url_sync: str = Field(default="sqlite:///nft_arbitrage.db", alias="DATABASE_URL_SYNC")
    pool_size: int = 5
    max_overflow: int = 5
    echo: bool = False


class RedisSettings(BaseSettings):
    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    ttl_seconds: int = 60


class AISettings(BaseSettings):
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    primary_provider: str = "anthropic"
    fallback_provider: str = "openai"
    model_anthropic: str = "claude-sonnet-4-20250514"
    model_openai: str = "gpt-4o"
    max_retries: int = 3
    timeout_seconds: int = 30


class BlockchainSettings(BaseSettings):
    eth_rpc_url: str = Field(default="", alias="ETH_RPC_URL")
    base_rpc_url: str = Field(default="https://base-rpc.publicnode.com", alias="BASE_RPC_URL")
    eth_private_key: str = Field(default="", alias="ETH_PRIVATE_KEY")
    flashbots_rpc_url: str = Field(default="https://rpc.flashbots.net/fast", alias="FLASHBOTS_RPC_URL")
    chain_id: int = 1

    def rpc_url_for_chain(self, chain: str) -> str:
        if chain == "base":
            return self.base_rpc_url
        return self.eth_rpc_url

    def chain_id_for(self, chain: str) -> int:
        if chain == "base":
            return 8453
        return 1


class MarketplaceSettings(BaseSettings):
    opensea_api_key: str = Field(default="", alias="OPENSEA_API_KEY")
    moralis_api_key: str = Field(default="", alias="MORALIS_API_KEY")
    nansen_api_key: str = Field(default="", alias="NANSEN_API_KEY")


class TelegramSettings(BaseSettings):
    bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    enabled: bool = True


class Settings:
    """Master settings object combining all config sources."""

    def __init__(self):
        self.yaml_settings = load_yaml("settings.yaml")
        self.yaml_strategies = load_yaml("strategies.yaml")

        self.db = DatabaseSettings()
        self.redis = RedisSettings()
        self.ai = AISettings()
        self.blockchain = BlockchainSettings()
        self.marketplace = MarketplaceSettings()
        self.telegram = TelegramSettings()

        self.environment = os.getenv("ENVIRONMENT", self.yaml_settings.get("system", {}).get("environment", "development"))
        self.log_level = os.getenv("LOG_LEVEL", self.yaml_settings.get("system", {}).get("log_level", "INFO"))
        self.secret_key = os.getenv("SECRET_KEY", "change-me")

    @property
    def collections(self) -> list[dict]:
        return self.yaml_settings.get("collections", [])

    @property
    def ingestion(self) -> dict:
        return self.yaml_settings.get("ingestion", {})

    @property
    def cost_engine(self) -> dict:
        return self.yaml_settings.get("cost_engine", {})

    @property
    def strategies(self) -> dict:
        return self.yaml_settings.get("strategies", {})

    @property
    def strategy_configs(self) -> dict:
        return self.yaml_strategies

    @property
    def risk(self) -> dict:
        return self.yaml_settings.get("risk", {})

    @property
    def self_improvement(self) -> dict:
        return self.yaml_settings.get("self_improvement", {})

    @property
    def trend_scoring(self) -> dict:
        return self.yaml_settings.get("trend_scoring", {})

    @property
    def wash_detection(self) -> dict:
        return self.yaml_settings.get("wash_detection", {})

    @property
    def execution(self) -> dict:
        return self.yaml_settings.get("execution", {})

    @property
    def scheduling(self) -> dict:
        return self.yaml_settings.get("scheduling", {})

    @property
    def observation_loop(self) -> dict:
        return self.yaml_settings.get("observation_loop", {})

    @property
    def forecast_gate(self) -> dict:
        return self.yaml_settings.get("forecast_gate", {})

    @property
    def notifications(self) -> dict:
        return self.yaml_settings.get("notifications", {})


@lru_cache()
def get_settings() -> Settings:
    return Settings()
