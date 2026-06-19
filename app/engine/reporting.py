import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.engine.state import TestState


def build_account_chart(state: TestState) -> str:
    dates   = [b["date"]     for b in state.equity_curve]
    equity  = [b["equity"]   for b in state.equity_curve]
    balance = [b["balance"]  for b in state.equity_curve]
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
        title="Account Metrics",
        height=600,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig.to_html(full_html=True, include_plotlyjs="cdn")
