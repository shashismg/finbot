"""Streamlit UI for FinBot.  Run: streamlit run app.py"""
import plotly.graph_objects as go
import streamlit as st

from finbot.agent import TOOL_LABELS, run
from finbot.config import DISCLAIMER
from finbot.schemas import StockVerdict
from finbot.tools.market_data import get_history
from finbot.tools.technicals import sma

st.set_page_config(page_title="FinBot", page_icon="📈", layout="wide")

VERDICT_COLORS = {"BUY": "#1a7f37", "HOLD": "#b08800", "AVOID": "#cf222e", "INSUFFICIENT_DATA": "#57606a"}


def price_chart(symbol: str) -> go.Figure | None:
    try:
        df = get_history(symbol)
    except Exception:
        return None
    close = df["Close"]
    s50, s200 = sma(close, 50), sma(close, 200)
    df, s50, s200 = df.iloc[-252:], s50.iloc[-252:], s200.iloc[-252:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=s50.index, y=s50, name="SMA 50", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=s200.index, y=s200, name="SMA 200", line=dict(dash="dash")))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"),
                      title=f"{symbol}: last 1 year")
    return fig


def render_verdict(v: StockVerdict) -> None:
    if not v.is_stock_query:
        st.info(v.summary)
        return
    color = VERDICT_COLORS[v.verdict]
    st.markdown(
        f"""<div style="border-left:6px solid {color};padding:12px 16px;border-radius:6px;background:rgba(127,127,127,.08)">
        <div style="font-size:1.1rem">{v.company} <code>{v.ticker}</code> {v.currency}</div>
        <div style="font-size:2rem;font-weight:700;color:{color}">{v.verdict.replace('_', ' ')}</div>
        <div>Confidence <b>{v.confidence}%</b> · Horizon <b>{v.time_horizon or 'n/a'}</b></div></div>""",
        unsafe_allow_html=True,
    )
    st.progress(v.confidence / 100)
    st.write(v.summary)

    bull, bear = st.columns(2)
    with bull:
        st.subheader("Bull case")
        for p in v.bull_points:
            st.markdown(f"- {p}")
    with bear:
        st.subheader("Bear case")
        for p in v.bear_points:
            st.markdown(f"- {p}")

    left, right = st.columns([3, 2])
    with left:
        if v.ticker and (fig := price_chart(v.ticker)):
            st.plotly_chart(fig, use_container_width=True)
    with right:
        if v.key_metrics:
            st.subheader("Key metrics")
            st.table({"Metric": list(v.key_metrics), "Value": list(v.key_metrics.values())})

    if v.sources:
        with st.expander("Sources"):
            for s in v.sources:
                st.markdown(f"- {s}")


st.title("📈 FinBot")
st.caption("Stock research agent for US & Indian markets: BUY / HOLD / AVOID with reasoning.")

if "history" not in st.session_state:
    st.session_state.history = []  # list of (query, StockVerdict)

for q, v in st.session_state.history:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        render_verdict(v)

query = st.chat_input("e.g. Should I buy Tata Motors?  /  Is NVDA a good buy right now?")
if query:
    with st.chat_message("user"):
        st.write(query)
    with st.chat_message("assistant"):
        with st.status("Researching…", expanded=True) as status:
            def on_step(name: str, args: dict) -> None:
                arg = next(iter(args.values()), "")
                st.write(f"{TOOL_LABELS[name]}… `{arg}`")
            try:
                verdict = run(query, on_step=on_step)
                status.update(label="Research complete", state="complete", expanded=False)
            except Exception as exc:
                status.update(label="Research failed", state="error")
                st.error(f"Something went wrong: {exc}")
                st.stop()
        render_verdict(verdict)
    st.session_state.history.append((query, verdict))

st.divider()
st.caption(f"⚠️ {DISCLAIMER}")
