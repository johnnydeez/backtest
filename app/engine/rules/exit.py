import math

# Exit rules return a reason string if they trigger, or None if they don't.
# The loop iterates all active exit rules and closes on the first one that fires.
# This keeps the loop agnostic about why a trade closes.


class ATRStopLossRule:
    """
    Exits a long position if the current bar's low touches or crosses the stop loss level.
    The stop loss is set at entry as: entry_price - (ATR * multiplier).
    Requires 'low' key in the bar dict and the stop loss level from TestState.
    """

    def evaluate(self, bar: dict, state) -> str | None:
        stop_loss = state.stop_loss
        if stop_loss is None or math.isnan(stop_loss):
            return None

        if bar["low"] <= stop_loss:
            return "stop_loss"

        return None


class NDayLowTakeProfitRule:
    """
    Exits a long trade when the bar's close drops below the N-day low close.
    If close_only_if_profitable is true, the rule only fires when the trade is in profit.
    config expects: { "indicator": { ... }, "close_only_if_profitable": true|false }
    """

    def __init__(self, config: dict):
        self.close_only_if_profitable = config.get("close_only_if_profitable", False)

    def evaluate(self, bar: dict, state) -> str | None:
        n_day_low = bar.get("n_day_low")
        if n_day_low is None or (isinstance(n_day_low, float) and math.isnan(n_day_low)):
            return None

        if self.close_only_if_profitable and bar["close"] <= state.entry_price:
            return None

        if bar["close"] < n_day_low:
            return "take_profit"

        return None


class TimeoutRule:
    """
    Exits a trade after N bars regardless of price.
    config expects: { "bars": <int> }
    """

    def __init__(self, config: dict):
        self.bars = config.get("bars", 0)

    def evaluate(self, bar: dict, state) -> str | None:
        # TODO: implement bar counting since entry
        return None
