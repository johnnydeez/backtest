"""
Pure functions for forex trading math.
All functions are stateless and operate only on their arguments.
"""


def pip_multiplier(pair: str) -> float:
    return 0.01 if pair.endswith("JPY") else 0.0001


def pip_dollar_value(pair: str, units: int) -> float:
    # TODO: only correct for USD-quoted pairs (EUR_USD, GBP_USD, AUD_USD, etc.)
    # USD-base pairs (USD_JPY, USD_CAD, USD_CHF): need entry_price → (units × pip_size) / entry_price
    # Cross pairs (EUR_JPY, GBP_JPY, EUR_GBP): need a secondary USD rate not present in single-pair data
    # Fix requires passing entry_price into this function and adding pair-type detection.
    return (units / 100000) * 10


def pip_profit(pair: str, direction: str, entry_price: float, exit_price: float) -> float:
    multiplier = pip_multiplier(pair)
    if direction == "long":
        return (exit_price - entry_price) / multiplier
    return (entry_price - exit_price) / multiplier
