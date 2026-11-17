"""Key fundamental ratios from yfinance."""
import yfinance as yf
from langchain_core.tools import tool

from ._util import error, to_json

# yfinance info key -> friendly name, multiplier (fractions -> %)
_FIELDS: dict[str, tuple[str, float]] = {
    "marketCap": ("market_cap", 1),
    "trailingPE": ("pe_trailing", 1),
    "forwardPE": ("pe_forward", 1),
    "priceToBook": ("price_to_book", 1),
    "trailingPegRatio": ("peg_ratio", 1),
    "enterpriseToEbitda": ("ev_to_ebitda", 1),
    "returnOnEquity": ("roe_pct", 100),
    "returnOnAssets": ("roa_pct", 100),
    "profitMargins": ("net_margin_pct", 100),
    "operatingMargins": ("operating_margin_pct", 100),
    "revenueGrowth": ("revenue_growth_yoy_pct", 100),
    "earningsGrowth": ("earnings_growth_yoy_pct", 100),
    "debtToEquity": ("debt_to_equity_ratio", 0.01),  # yfinance reports this in % (8.57 -> 0.0857x)
    "currentRatio": ("current_ratio", 1),
    "freeCashflow": ("free_cash_flow", 1),
    "dividendYield": ("dividend_yield_pct", 1),  # yfinance already returns this in %
    "beta": ("beta", 1),
    "heldPercentInsiders": ("insider_holding_pct", 100),
    "targetMeanPrice": ("analyst_target_mean", 1),
    "recommendationKey": ("analyst_consensus", 1),
    "numberOfAnalystOpinions": ("analyst_count", 1),
}


def extract_fundamentals(info: dict) -> dict:
    out = {
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
    }
    for key, (name, mult) in _FIELDS.items():
        val = info.get(key)
        if val is None:
            continue
        out[name] = val * mult if isinstance(val, (int, float)) and not isinstance(val, bool) and mult != 1 else val
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    target = info.get("targetMeanPrice")
    if price and target:
        out["analyst_upside_pct"] = (target / price - 1) * 100
    return {k: v for k, v in out.items() if v is not None}


@tool
def get_fundamentals(symbol: str) -> str:
    """Get fundamentals for a yfinance symbol: valuation (P/E, P/B, PEG), profitability (ROE, margins),
    balance sheet (debt/equity), growth, dividend yield and analyst consensus/target price."""
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception as exc:
        return error(f"Could not fetch fundamentals for '{symbol}': {exc}")
    data = extract_fundamentals(info)
    if len(data) <= 2:
        return error(f"No fundamental data available for '{symbol}'.")
    return to_json({"symbol": symbol, **data})
