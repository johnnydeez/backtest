import os
import pandas as pd
from app.engine.indicators import custom, library


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


class BacktestParams:
    """
    Loads historical data and pre-calculates all indicators needed for the backtest.
    Produces a list of bar dicts that BacktestLoop iterates over.

    Each bar dict contains:
        timestamp, open, high, low, close  — raw price data
        n_day_high                         — pre-calculated breakout level (custom indicator)
        atr                                — pre-calculated ATR value (library indicator)
    """

    def __init__(self, strategy: dict):
        self.strategy = strategy
        self.pair = strategy["fx_pairs"][0]
        self.direction = strategy["direction"]
        self.duration = strategy.get("duration")

        rules = strategy["rules"]
        self.breakout_period = rules["entry"]["indicator"]["params"]["high"]

        stop_loss_config = rules.get("exit", {}).get("stop_loss", {})
        self.atr_period = stop_loss_config.get("indicator", {}).get("params", {}).get("period", 14)
        self.atr_multiplier = stop_loss_config.get("multiplier", 1)

        self.bars = self._build_bars()

    def _load_data(self) -> pd.DataFrame:
        files = sorted([
            f for f in os.listdir(DATA_DIR)
            if f.endswith(f"_{self.pair}.csv")
        ])
        if not files:
            raise FileNotFoundError(f"No data files found for {self.pair} in {DATA_DIR}")

        if self.duration is not None:
            start = self.duration.get("start")
            end = self.duration.get("end")
            files = [
                f for f in files
                if (start is None or int(f.split("_")[0]) >= start)
                and (end is None or int(f.split("_")[0]) <= end)
            ]

        frames = [
            pd.read_csv(os.path.join(DATA_DIR, f), parse_dates=["timestamp"])
            for f in files
        ]
        df = pd.concat(frames).sort_values("timestamp").reset_index(drop=True)
        return df

    def _build_bars(self) -> list[dict]:
        df = self._load_data()

        df["n_day_high"] = custom.n_day_high(df["high"], self.breakout_period)
        df["atr"] = library.atr(df["high"], df["low"], df["close"], self.atr_period)

        take_profit_config = self.strategy.get("rules", {}).get("exit", {}).get("take_profit", {})
        if take_profit_config:
            period = take_profit_config["indicator"]["params"]["low"]
            df["n_day_low"] = custom.n_day_low(df["close"], period)

        return df.to_dict(orient="records")
