# FinBot 📈

A LangChain agent that researches a stock and gives a **BUY / HOLD / AVOID** verdict, with its confidence, the bull and bear cases, key metrics and sources. It covers **US** stocks (e.g. `AAPL`) and **Indian** stocks (e.g. `RELIANCE.NS`, `TCS.BO`).

> FinBot is for educational purposes only and is not financial advice.

## How it works
`create_agent` (LangChain v1 / LangGraph) + Groq `openai/gpt-oss-120b` + six tools:

| Tool | Source | Returns |
|---|---|---|
| `resolve_ticker` | yfinance search | company name/symbol → ticker (prefers NSE for Indian names) |
| `get_price_snapshot` | yfinance | price, 52w range, 1m/6m/1y returns |
| `get_fundamentals` | yfinance | P/E, P/B, PEG, ROE, margins, D/E, growth, analyst target |
| `get_technicals` | pandas | SMA50/200, golden/death cross, RSI14, MACD, volatility |
| `get_news` | yfinance | recent headlines |
| `web_search` | DuckDuckGo | analyst views, recent events |

The tools do all the arithmetic, and the LLM only interprets the numbers. The final answer is a typed `StockVerdict` model (see [finbot/schemas.py](finbot/schemas.py)).

## Setup
```bash
export GROQ_API_KEY=gsk_...  # in ~/.zshrc: read from the system env only, never from .env
uv sync                     # or: pip install -r requirements.txt
```

## Run
```bash
uv run streamlit run app.py                       # web UI
uv run python cli.py "Should I buy Tata Motors?"  # terminal
uv run pytest                                     # all tests
uv run pytest -m "not live"                       # offline tests only
```

## Layout
```
finbot/agent.py      agent construction + run(query, on_step)
finbot/prompts.py    analyst system prompt (research checklist + decision rules)
finbot/schemas.py    StockVerdict structured output
finbot/tools/        ticker, market_data, fundamentals, technicals, news
app.py / cli.py      Streamlit UI / terminal client
```
