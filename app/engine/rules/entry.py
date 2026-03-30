import math

# TODO: add a rule registry that maps JSON "name" values to rule classes.
# e.g. ENTRY_RULES = {"breakout": BreakoutEntryRule, "rsi": RSIEntryRule, ...}
# The engine can then look up and instantiate the correct rule from the strategy JSON
# without any changes to the loop.


class BreakoutEntryRule:
    """
    Enters long when the current bar's high breaks above the N-day high.
    Requires 'high' and 'n_day_high' keys in the bar dict.
    n_day_high is pre-calculated in BacktestParams (excludes current bar to avoid look-ahead bias).
    """

    def evaluate(self, bar: dict) -> bool:
        n_day_high = bar["n_day_high"]

        if n_day_high is None or math.isnan(n_day_high):
            return False

        return bar["high"] > n_day_high
