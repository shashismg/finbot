"""Resolve a company name or symbol to a yfinance ticker."""
import yfinance as yf
from langchain_core.tools import tool

from ._util import error, to_json

_EQUITY_TYPES = {"EQUITY", "ETF"}
_INDIAN_SUFFIXES = (".NS", ".BO")


def search_tickers(query: str, max_results: int = 8) -> list[dict]:
    quotes = yf.Search(query, max_results=max_results, news_count=0).quotes or []
    out = []
    for q in quotes:
        if q.get("quoteType") not in _EQUITY_TYPES or not q.get("symbol"):
            continue
        out.append(
            {
                "symbol": q["symbol"],
                "name": q.get("longname") or q.get("shortname") or "",
                "exchange": q.get("exchDisp") or q.get("exchange") or "",
                "type": q.get("quoteType"),
            }
        )
    return out


def pick_best(candidates: list[dict]) -> dict | None:
    """Prefer NSE over BSE for Indian names; otherwise keep Yahoo's ranking."""
    if not candidates:
        return None
    top = candidates[0]
    if top["symbol"].endswith(".BO"):
        base = top["symbol"][:-3]
        for c in candidates:
            if c["symbol"] == f"{base}.NS":
                return c
    return top


@tool
def resolve_ticker(company_or_symbol: str) -> str:
    """Find the yfinance ticker symbol for a company name or symbol.

    Works for US stocks (e.g. 'Apple', 'NVDA') and Indian stocks (e.g. 'Tata Motors',
    'RELIANCE.NS'). Returns the best match plus other candidates.
    """
    try:
        candidates = search_tickers(company_or_symbol)
        if not candidates and not company_or_symbol.upper().endswith(_INDIAN_SUFFIXES):
            # Yahoo search sometimes misses Indian names; retry with an NSE hint.
            candidates = search_tickers(f"{company_or_symbol} NSE")
    except Exception as exc:  # network / API errors
        return error(f"Ticker search failed: {exc}")
    best = pick_best(candidates)
    if best is None:
        return error(f"No listed stock found for '{company_or_symbol}'.")
    return to_json({"best_match": best, "other_candidates": [c for c in candidates if c is not best][:4]})
