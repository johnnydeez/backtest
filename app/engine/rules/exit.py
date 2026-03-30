import math

# TODO: add a rule registry that maps JSON "name" values to rule classes.
# e.g. EXIT_RULES = {"atr_stop": ATRStopLossRule, "trailing": TrailingStopRule, ...}

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
