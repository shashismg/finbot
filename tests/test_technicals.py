import numpy as np
import pandas as pd
import pytest

from finbot.tools.fundamentals import extract_fundamentals
from finbot.tools.news import parse_news_item
from finbot.tools.technicals import compute_technicals, macd, rsi, sma
from finbot.tools.ticker import pick_best


def _df(close: list[float] | np.ndarray) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(close), freq="B")
    return pd.DataFrame({"Close": close, "Volume": 1000}, index=idx)


def test_sma():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert sma(s, 5).iloc[-1] == 3


def test_rsi_extremes():
    up = pd.Series(np.arange(1, 60, dtype=float))
    down = pd.Series(np.arange(60, 1, -1, dtype=float))
    assert rsi(up).iloc[-1] == pytest.approx(100)
    assert rsi(down).iloc[-1] == pytest.approx(0)


def test_rsi_bounds_on_random_walk():
    rng = np.random.default_rng(0)
    s = pd.Series(100 + rng.normal(0, 1, 300).cumsum())
    vals = rsi(s).dropna()
    assert ((vals >= 0) & (vals <= 100)).all()


def test_macd_bullish_in_uptrend():
    line, signal = macd(pd.Series(np.linspace(100, 200, 100) ** 1.01))
    assert line.iloc[-1] > 0


def test_compute_technicals_uptrend():
    out = compute_technicals(_df(np.linspace(100, 300, 260)))
    assert out["price_vs_sma50"] == "above"
    assert out["price_vs_sma200"] == "above"
    assert out["trend"].startswith("golden cross")
    assert out["rsi_state"] == "overbought"


def test_compute_technicals_short_history_has_no_sma200():
    out = compute_technicals(_df(np.linspace(100, 110, 60)))
    assert "price_vs_sma200" not in out


def test_pick_best_prefers_nse():
    c = [{"symbol": "TATAMOTORS.BO"}, {"symbol": "TATAMOTORS.NS"}]
    assert pick_best(c)["symbol"] == "TATAMOTORS.NS"
    assert pick_best([{"symbol": "AAPL"}])["symbol"] == "AAPL"
    assert pick_best([]) is None


def test_extract_fundamentals_converts_fractions():
    out = extract_fundamentals({"longName": "X", "returnOnEquity": 0.25, "currentPrice": 100, "targetMeanPrice": 120})
    assert out["roe_pct"] == pytest.approx(25)
    assert out["analyst_upside_pct"] == pytest.approx(20)


def test_parse_news_both_formats():
    new = {"content": {"title": "T", "provider": {"displayName": "P"}, "canonicalUrl": {"url": "u"}}}
    old = {"title": "T", "publisher": "P", "link": "u"}
    for item in (new, old):
        n = parse_news_item(item)
        assert (n["title"], n["publisher"], n["url"]) == ("T", "P", "u")
    assert parse_news_item({}) is None


def test_debt_to_equity_is_a_ratio():
    assert extract_fundamentals({"longName": "X", "debtToEquity": 8.57})["debt_to_equity_ratio"] == pytest.approx(0.0857)
