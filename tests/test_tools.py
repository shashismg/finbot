"""Live smoke tests (network). Skip with: pytest -m 'not live'"""
import json

import pytest

from finbot.tools import get_fundamentals, get_news, get_price_snapshot, get_technicals, resolve_ticker

pytestmark = pytest.mark.live


@pytest.mark.parametrize("query,expected", [("Apple", "AAPL"), ("Reliance Industries", "RELIANCE.NS")])
def test_resolve_ticker(query, expected):
    out = json.loads(resolve_ticker.invoke({"company_or_symbol": query}))
    assert out["best_match"]["symbol"] == expected


@pytest.mark.parametrize("symbol", ["AAPL", "RELIANCE.NS"])
def test_data_tools(symbol):
    snap = json.loads(get_price_snapshot.invoke({"symbol": symbol}))
    assert snap["price"] > 0
    tech = json.loads(get_technicals.invoke({"symbol": symbol}))
    assert 0 <= tech["rsi14"] <= 100
    fund = json.loads(get_fundamentals.invoke({"symbol": symbol}))
    assert "error" not in fund
    news = json.loads(get_news.invoke({"symbol": symbol}))
    assert isinstance(news, list) or "error" in news


def test_bad_symbol_returns_error():
    out = json.loads(get_price_snapshot.invoke({"symbol": "ZZZZNOTREAL123"}))
    assert "error" in out
