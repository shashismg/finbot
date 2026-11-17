"""Company news (yfinance) and general web search (DuckDuckGo)."""
import yfinance as yf
from ddgs import DDGS
from langchain_core.tools import tool

from ._util import error, to_json


def parse_news_item(item: dict) -> dict | None:
    """Handle both the old flat and the new nested ('content') yfinance news formats."""
    c = item.get("content") or item
    title = c.get("title")
    if not title:
        return None
    url = (c.get("canonicalUrl") or {}).get("url") or (c.get("clickThroughUrl") or {}).get("url") or c.get("link")
    provider = (c.get("provider") or {}).get("displayName") or c.get("publisher")
    return {
        "title": title,
        "publisher": provider,
        "date": c.get("pubDate") or c.get("providerPublishTime"),
        "summary": (c.get("summary") or "")[:300],
        "url": url,
    }


@tool
def get_news(symbol: str) -> str:
    """Get the latest news headlines (title, publisher, date, summary, url) for a yfinance symbol."""
    try:
        raw = yf.Ticker(symbol).news or []
    except Exception as exc:
        return error(f"Could not fetch news for '{symbol}': {exc}")
    items = [n for n in (parse_news_item(r) for r in raw[:10]) if n]
    if not items:
        return error(f"No recent news found for '{symbol}'. Try web_search instead.")
    return to_json(items)


@tool
def web_search(query: str) -> str:
    """Search the web (DuckDuckGo) for recent analyst views, earnings results or events about a company.
    Use specific queries, e.g. 'Infosys Q2 results analyst outlook'."""
    try:
        results = DDGS().text(query, max_results=6) or []
    except Exception as exc:
        return error(f"Web search failed: {exc}")
    return to_json([{"title": r.get("title"), "snippet": r.get("body"), "url": r.get("href")} for r in results])
