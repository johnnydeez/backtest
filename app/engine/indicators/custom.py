import pandas as pd


def n_day_high(high: pd.Series, period: int) -> pd.Series:
    """
    Returns the highest high over the previous N bars, excluding the current bar.
    Used to detect breakout entries without look-ahead bias.

    Example: with period=20, the value at bar[i] is max(high[i-20 : i])
    """
    return high.shift(1).rolling(window=period).max()


def n_day_low(close: pd.Series, period: int) -> pd.Series:
    """
    Returns the lowest close over the previous N bars, excluding the current bar.
    Used to detect trend exhaustion exits without look-ahead bias.

    Example: with period=10, the value at bar[i] is min(close[i-10 : i])
    """
    return close.shift(1).rolling(window=period).min()
