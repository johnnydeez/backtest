from app.engine.calculations import pip_dollar_value, pip_profit


class TestState:
    def __init__(self, initial_balance: float = 10000.0, units: int = 100000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.peak_equity = initial_balance
        self.max_drawdown = 0.0
        self.units = units

        self.in_position = False
        self.entry_price = None
        self.entry_date = None
        self.stop_loss = None

        self.active_trade = None
        self.closed_trades = []
        self.equity_curve = []

    def open_position(self, pair: str, date, price: float, stop_loss: float):
        self.in_position = True
        self.entry_price = price
        self.entry_date = date
        self.stop_loss = stop_loss
        self.active_trade = {
            "pair": pair,
            "direction": "long",
            "entry_date": str(date),
            "entry_price": price,
            "stop_loss": stop_loss,
            "pip_dollar_value": pip_dollar_value(pair, self.units),
        }

    def close_position(self, pair: str, date, price: float, reason: str):
        pips = pip_profit(pair, self.active_trade["direction"], self.entry_price, price)
        dollars = pips * self.active_trade["pip_dollar_value"]

        self.balance += dollars

        trade_record = {
            **self.active_trade,
            "exit_date": str(date),
            "exit_price": price,
            "exit_reason": reason,
            "pip_profit": round(pips, 1),
            "dollar_profit": round(dollars, 2),
        }
        self.closed_trades.append(trade_record)

        self.in_position = False
        self.entry_price = None
        self.entry_date = None
        self.stop_loss = None
        self.active_trade = None

    def update_drawdown(self, date, current_price: float, pair: str):
        if self.in_position:
            pips = pip_profit(pair, self.active_trade["direction"], self.entry_price, current_price)
            unrealized = pips * self.active_trade["pip_dollar_value"]
        else:
            unrealized = 0.0

        equity = self.balance + unrealized
        self.peak_equity = max(self.peak_equity, equity)
        drawdown = self.peak_equity - equity
        self.max_drawdown = max(self.max_drawdown, drawdown)

        self.equity_curve.append({
            "date": date,
            "equity": round(equity, 2),
            "balance": round(self.balance, 2),
            "drawdown": round(-drawdown, 2),
        })
