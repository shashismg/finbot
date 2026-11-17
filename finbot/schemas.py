"""Structured output returned by the agent."""
from typing import Literal

from pydantic import BaseModel, Field


class StockVerdict(BaseModel):
    """Final research verdict for a single stock."""

    is_stock_query: bool = Field(
        description="False if the user did not ask about a stock/company; then fill only `summary` with a polite redirect."
    )
    ticker: str = Field(default="", description="Resolved yfinance symbol, e.g. AAPL or RELIANCE.NS")
    company: str = Field(default="", description="Company name")
    currency: str = Field(default="", description="Trading currency, e.g. USD or INR")
    verdict: Literal["BUY", "HOLD", "AVOID", "INSUFFICIENT_DATA"] = Field(
        default="INSUFFICIENT_DATA", description="Overall recommendation"
    )
    confidence: int = Field(default=0, ge=0, le=100, description="Confidence in the verdict, 0-100")
    time_horizon: str = Field(default="", description="Horizon the verdict applies to, e.g. '6-12 months'")
    summary: str = Field(description="2-4 sentence plain-English rationale (or redirect message)")
    bull_points: list[str] = Field(default_factory=list, description="Reasons supporting the stock")
    bear_points: list[str] = Field(default_factory=list, description="Risks and reasons against")
    key_metrics: dict[str, str] = Field(
        default_factory=dict,
        description="Important numbers exactly as returned by tools, e.g. {'P/E': '28.4', 'RSI14': '61.2'}",
    )
    sources: list[str] = Field(default_factory=list, description="URLs of news/web sources used")
