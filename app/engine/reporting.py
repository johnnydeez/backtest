import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.engine.state import TestState


def build_charts(state: TestState, bars: list[dict]) -> str:
    account_html = _build_account_fig(state).to_html(full_html=False, include_plotlyjs="cdn")
    trades_html = _build_trades_fig(state, bars).to_html(full_html=False, include_plotlyjs=False)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: sans-serif; margin: 24px; background: #fafafa; }}
    h2 {{ color: #333; margin-top: 32px; }}
  </style>
</head>
<body>
  <h2>Account Metrics</h2>
  {account_html}
  <h2>Price &amp; Trades</h2>
  {trades_html}
</body>
</html>"""


def _build_account_fig(state: TestState) -> go.Figure:
    dates    = [b["date"]     for b in state.equity_curve]
    equity   = [b["equity"]   for b in state.equity_curve]
    balance  = [b["balance"]  for b in state.equity_curve]
    drawdown = [b["drawdown"] for b in state.equity_curve]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.04,
        subplot_titles=("Equity & Balance", "Drawdown ($)"),
    )

    fig.add_trace(
        go.Scatter(x=dates, y=equity, name="Equity", line=dict(color="#2196F3", width=1.5)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=dates, y=balance, name="Balance", line=dict(color="#9E9E9E", width=1, dash="dot")),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=dates, y=drawdown,
            name="Drawdown",
            fill="tozeroy",
            line=dict(color="#F44336", width=1),
            fillcolor="rgba(244, 67, 54, 0.2)",
        ),
        row=2, col=1,
    )

    fig.update_yaxes(title_text="Account Value ($)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown ($)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_layout(
        height=600,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def _build_trades_fig(state: TestState, bars: list[dict]) -> go.Figure:
    timestamps = [b["timestamp"] for b in bars]
    opens      = [b["open"]      for b in bars]
    highs      = [b["high"]      for b in bars]
    lows       = [b["low"]       for b in bars]
    closes     = [b["close"]     for b in bars]

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=timestamps,
        open=opens, high=highs, low=lows, close=closes,
        name="Price",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ))

    trades = state.closed_trades
    if trades:
        entry_dates  = [t["entry_date"]  for t in trades]
        entry_prices = [t["entry_price"] for t in trades]
        exit_dates   = [t["exit_date"]   for t in trades]
        exit_prices  = [t["exit_price"]  for t in trades]

        entry_hover = [
            f"<b>Entry</b><br>Price: {t['entry_price']}<br>Stop: {t['stop_loss']}"
            for t in trades
        ]
        exit_hover = [
            f"<b>Exit</b> ({t['exit_reason']})<br>"
            f"Price: {t['exit_price']}<br>"
            f"P&L: ${t['dollar_profit']:+.2f} ({t['pip_profit']:+.1f} pips)"
            for t in trades
        ]

        fig.add_trace(go.Scatter(
            x=entry_dates, y=entry_prices,
            mode="markers",
            name="Entry",
            marker=dict(symbol="triangle-up", color="#26a69a", size=12, line=dict(width=1, color="#1a7a70")),
            hovertemplate="%{text}<extra></extra>",
            text=entry_hover,
        ))

        fig.add_trace(go.Scatter(
            x=exit_dates, y=exit_prices,
            mode="markers",
            name="Exit",
            marker=dict(symbol="triangle-down", color="#ef5350", size=12, line=dict(width=1, color="#b71c1c")),
            hovertemplate="%{text}<extra></extra>",
            text=exit_hover,
        ))

        # Stop loss line for each trade
        for trade in trades:
            fig.add_shape(
                type="line",
                x0=trade["entry_date"], x1=trade["exit_date"],
                y0=trade["stop_loss"],  y1=trade["stop_loss"],
                line=dict(color="rgba(239, 83, 80, 0.5)", width=1, dash="dot"),
            )

    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        yaxis_title="Price",
        xaxis_title="Date",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig
