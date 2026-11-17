"""Technical indicators computed with pandas (no LLM arithmetic)."""
import pandas as pd
from langchain_core.tools import tool

from ._util import error, to_json
from .market_data import get_history


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = gain / loss
    out = 100 - 100 / (1 + rs)
    return out.where(loss != 0, 100.0)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series]:
    line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    return line, line.ewm(span=signal, adjust=False).mean()


def annualized_volatility(close: pd.Series, days: int = 252) -> float:
    return close.pct_change().iloc[-days:].std() * (252**0.5) * 100


def compute_technicals(df: pd.DataFrame) -> dict:
    close = df["Close"]
    price = close.iloc[-1]
    s50, s200 = sma(close, 50), sma(close, 200)
    macd_line, signal_line = macd(close)
    r = rsi(close).iloc[-1]

    out: dict = {
        "price": price,
        "sma50": s50.iloc[-1],
        "sma200": s200.iloc[-1],
        "rsi14": r,
        "rsi_state": "overbought" if r > 70 else "oversold" if r < 30 else "neutral",
        "macd": macd_line.iloc[-1],
        "macd_signal": signal_line.iloc[-1],
        "macd_trend": "bullish" if macd_line.iloc[-1] > signal_line.iloc[-1] else "bearish",
        "annualized_volatility_pct": annualized_volatility(close),
    }
    if pd.notna(s50.iloc[-1]):
        out["price_vs_sma50"] = "above" if price > s50.iloc[-1] else "below"
    if pd.notna(s200.iloc[-1]):
        out["price_vs_sma200"] = "above" if price > s200.iloc[-1] else "below"
        out["trend"] = "golden cross (SMA50 > SMA200)" if s50.iloc[-1] > s200.iloc[-1] else "death cross (SMA50 < SMA200)"
        # Did a cross happen in the last 30 sessions?
        diff = (s50 - s200).dropna().iloc[-30:]
        if len(diff) > 1 and (diff.iloc[0] > 0) != (diff.iloc[-1] > 0):
            out["recent_cross"] = "crossed within last 30 sessions"
    return out


@tool
def get_technicals(symbol: str) -> str:
    """Get technical indicators for a yfinance symbol: SMA50/200 trend, RSI14, MACD and volatility."""
    try:
        df = get_history(symbol)
    except Exception as exc:
        return error(str(exc))
    if len(df) < 30:
        return error(f"Not enough price history for '{symbol}' ({len(df)} days).")
    return to_json({"symbol": symbol, **compute_technicals(df)})
