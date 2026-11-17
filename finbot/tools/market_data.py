"""Price history and snapshot."""
from functools import lru_cache

import pandas as pd
import yfinance as yf
from langchain_core.tools import tool

from ._util import error, to_json


@lru_cache(maxsize=64)
def get_history(symbol: str, period: str = "2y") -> pd.DataFrame:
    """Daily OHLCV history (cached per process). Raises ValueError if empty."""
    df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"No price history for '{symbol}'. Check the symbol.")
    return df


def pct_return(close: pd.Series, trading_days: int) -> float | None:
    if len(close) <= trading_days:
        return None
    return (close.iloc[-1] / close.iloc[-1 - trading_days] - 1) * 100


@tool
def get_price_snapshot(symbol: str) -> str:
    """Get the latest price, 52-week high/low and 1m/6m/1y returns (%) for a yfinance symbol."""
    try:
        df = get_history(symbol)
    except Exception as exc:
        return error(str(exc))
    close = df["Close"]
    last_year = close.iloc[-252:]
    price = close.iloc[-1]
    hi, lo = last_year.max(), last_year.min()
    return to_json(
        {
            "symbol": symbol,
            "as_of": df.index[-1].date().isoformat(),
            "price": price,
            "52w_high": hi,
            "52w_low": lo,
            "pct_below_52w_high": (1 - price / hi) * 100,
            "return_1m_pct": pct_return(close, 21),
            "return_6m_pct": pct_return(close, 126),
            "return_1y_pct": pct_return(close, 252),
            "avg_volume_3m": df["Volume"].iloc[-63:].mean(),
        }
    )
