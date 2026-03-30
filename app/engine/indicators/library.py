import pandas as pd
import pandas_ta as ta


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """
    Average True Range over N periods.
    Used to set stop loss distance relative to recent volatility.
    """
    return ta.atr(high=high, low=low, close=close, length=period)
