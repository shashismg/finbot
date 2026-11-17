"""The FinBot agent: Groq LLM + research tools + structured verdict."""
from collections.abc import Callable
from datetime import date
from functools import lru_cache

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq

from . import config
from .prompts import SYSTEM_PROMPT
from .schemas import StockVerdict
from .tools import ALL_TOOLS

TOOL_LABELS = {
    "resolve_ticker": "Resolving ticker",
    "get_price_snapshot": "Fetching price data",
    "get_fundamentals": "Fetching fundamentals",
    "get_technicals": "Computing technical indicators",
    "get_news": "Reading latest news",
    "web_search": "Searching the web",
}


class stock_verdict(StockVerdict):  # noqa: N801
    """Submit the final research verdict. Call this exactly once, after research is complete."""


# ToolStrategy names the final-answer tool after the class. gpt-oss models emit snake_case
# tool names, and Groq rejects calls to unregistered names, so register it as `stock_verdict`.
FINAL_ANSWER_TOOL = stock_verdict.__name__


@lru_cache(maxsize=1)
def build_agent():
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set in the system environment. Export it in ~/.zshrc (it is not read from .env).")
    llm = ChatGroq(model=config.GROQ_MODEL, temperature=config.GROQ_TEMPERATURE, api_key=config.GROQ_API_KEY)
    return create_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT.format(today=date.today().isoformat(), final_tool=FINAL_ANSWER_TOOL),
        response_format=ToolStrategy(stock_verdict),
    )


def run(query: str, on_step: Callable[[str, dict], None] | None = None) -> StockVerdict:
    """Research `query` and return a StockVerdict.

    `on_step(tool_name, args)` is called each time the agent calls a tool (for progress UIs).
    """
    agent = build_agent()
    final_state = None
    for state in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        config={"recursion_limit": 30},
        stream_mode="values",
    ):
        final_state = state
        last = state["messages"][-1]
        if on_step and isinstance(last, AIMessage):
            for call in last.tool_calls:
                if call["name"] in TOOL_LABELS:
                    on_step(call["name"], call["args"])

    verdict = (final_state or {}).get("structured_response")
    if verdict is None:
        raise RuntimeError("The agent finished without producing a verdict.")
    return StockVerdict.model_validate(verdict.model_dump())
