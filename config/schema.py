# python/valuecell_trader/config/schema.py
"""
Configuration schema and validators for ValueCell AI Trader
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import yaml
from pathlib import Path


class UniverseConfig(BaseModel):
    """Universe configuration for stocks to trade"""

    tickers: List[str] = Field(..., description="List of ticker symbols")
    min_adv_usd: float = Field(
        5_000_000, description="Minimum average daily volume in USD"
    )


class RiskConfig(BaseModel):
    """Risk management configuration"""

    kelly_scale: float = Field(
        0.5, ge=0, le=1, description="Kelly criterion scaling factor"
    )
    max_total_exposure: float = Field(
        0.30, ge=0, le=1, description="Maximum total portfolio exposure"
    )
    max_per_name: float = Field(
        0.05, ge=0, le=1, description="Maximum exposure per ticker"
    )
    sector_cap: float = Field(
        0.15, ge=0, le=1, description="Maximum exposure per sector"
    )
    stop_pct: float = Field(0.02, ge=0, description="Stop loss percentage")
    tp_pct: float = Field(0.04, ge=0, description="Take profit percentage")
    timeout_days: int = Field(2, ge=1, description="Position timeout in days")


class ScoringConfig(BaseModel):
    """Scoring algorithm configuration"""

    z_threshold: float = Field(
        1.5, description="Z-score threshold for extension dampener"
    )
    alpha_ext: float = Field(
        0.4, ge=0, description="Extension dampener alpha parameter"
    )
    rsi_overbought: int = Field(
        75, ge=50, le=100, description="RSI overbought threshold"
    )
    volume_spike_mult: float = Field(
        3.0, ge=1, description="Volume spike multiplier threshold"
    )
    enter_threshold: float = Field(
        0.60, ge=0, le=1, description="Minimum score to enter position"
    )
    kneejerk_cut: float = Field(
        0.60, ge=0, le=1, description="P_drop threshold for knee-jerk exit"
    )


class SimulationConfig(BaseModel):
    """Backtesting simulation configuration"""

    slippage_bps: float = Field(10, ge=0, description="Slippage in basis points")
    fee_bps: float = Field(2, ge=0, description="Trading fees in basis points")
    bar_interval: str = Field("5m", description="Price bar interval (e.g., 1m, 5m, 1h)")


class TraderConfig(BaseModel):
    """Main configuration for ValueCell AI Trader"""

    universe: UniverseConfig
    risk: RiskConfig
    scoring: ScoringConfig
    simulation: SimulationConfig

    # Environment variables
    llm_provider: str = Field("openrouter", description="LLM provider")
    market_data_provider: str = Field("polygon", description="Market data provider")
    broker_mode: str = Field("paper", description="Broker mode (paper/live)")
    timezone: str = Field("America/New_York", description="Timezone for timestamps")
    news_sources: List[str] = Field(
        default=[
            "sec_edgar",
            "company_ir_rss",
            "businesswire",
            "prnewswire",
            "regulatory_feeds",
        ],
        description="Whitelisted news sources",
    )
    sim_latency_seconds: int = Field(
        600, ge=0, description="Simulated latency in seconds (10 min default)"
    )

    @validator("broker_mode")
    def validate_broker_mode(cls, v):
        if v not in ["paper", "live"]:
            raise ValueError('broker_mode must be "paper" or "live"')
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> "TraderConfig":
        """Load configuration from YAML file"""
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)

    def to_yaml(self, path: Path):
        """Save configuration to YAML file"""
        with open(path, "w") as f:
            yaml.dump(self.dict(), f, default_flow_style=False)


# Example default configuration
DEFAULT_CONFIG = {
    "universe": {
        "tickers": ["AAPL", "MSFT", "NVDA", "META", "LCID"],
        "min_adv_usd": 5_000_000,
    },
    "risk": {
        "kelly_scale": 0.5,
        "max_total_exposure": 0.30,
        "max_per_name": 0.05,
        "sector_cap": 0.15,
        "stop_pct": 0.02,
        "tp_pct": 0.04,
        "timeout_days": 2,
    },
    "scoring": {
        "z_threshold": 1.5,
        "alpha_ext": 0.4,
        "rsi_overbought": 75,
        "volume_spike_mult": 3.0,
        "enter_threshold": 0.60,
        "kneejerk_cut": 0.60,
    },
    "simulation": {"slippage_bps": 10, "fee_bps": 2, "bar_interval": "5m"},
    "llm_provider": "openrouter",
    "market_data_provider": "polygon",
    "broker_mode": "paper",
    "timezone": "America/New_York",
    "news_sources": [
        "sec_edgar",
        "company_ir_rss",
        "businesswire",
        "prnewswire",
        "regulatory_feeds",
    ],
    "sim_latency_seconds": 600,
}


def create_default_config(path: Path):
    """Create a default configuration file"""
    config = TraderConfig(**DEFAULT_CONFIG)
    config.to_yaml(path)
