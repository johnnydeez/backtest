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

    def _pip_multiplier(self, pair: str) -> float:
        return 0.01 if pair.endswith("JPY") else 0.0001

    def _pip_dollar_value(self, pair: str) -> float:
        # TODO: currently only correct for USD-quoted pairs (e.g. EUR_USD)
        # Needs to handle JPY pairs, inverse pairs (USD_JPY), and cross pairs (GBP_JPY)
        return (self.units / 100000) * 10

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
        }

    def close_position(self, pair: str, date, price: float, reason: str):
        pip_multiplier = self._pip_multiplier(pair)
        pip_profit = (price - self.entry_price) / pip_multiplier
        dollar_profit = pip_profit * self._pip_dollar_value(pair)

        self.balance += dollar_profit

        trade_record = {
            **self.active_trade,
            "exit_date": str(date),
            "exit_price": price,
            "exit_reason": reason,
            "pip_profit": round(pip_profit, 1),
            "dollar_profit": round(dollar_profit, 2),
        }
        self.closed_trades.append(trade_record)

        self.in_position = False
        self.entry_price = None
        self.entry_date = None
        self.stop_loss = None
        self.active_trade = None

    def update_drawdown(self, current_price: float, pair: str):
        if self.in_position:
            pip_multiplier = self._pip_multiplier(pair)
            pip_profit = (current_price - self.entry_price) / pip_multiplier
            unrealized = pip_profit * self._pip_dollar_value(pair)
        else:
            unrealized = 0.0

        equity = self.balance + unrealized
        self.peak_equity = max(self.peak_equity, equity)
        drawdown = self.peak_equity - equity
        self.max_drawdown = max(self.max_drawdown, drawdown)
