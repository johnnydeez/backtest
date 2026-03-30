import math
from app.engine.params import BacktestParams
from app.engine.state import TestState
from app.engine.rules.entry import BreakoutEntryRule
from app.engine.rules.exit import ATRStopLossRule


class BacktestLoop:
    """
    Iterates bar-by-bar over historical data and orchestrates entry/exit decisions.
    Delegates all decision logic to rule objects — contains no strategy logic itself.

    # TODO: when the rule registry is added, rules should be instantiated dynamically
    # from the strategy JSON rather than hardcoded here.
    """

    def __init__(self, params: BacktestParams, state: TestState):
        self.params = params
        self.state = state
        self.entry_rule = BreakoutEntryRule()
        # Exit rules are evaluated in order — first one that triggers closes the trade.
        # Add new exit rules here (take profit, time-based, etc.) as they are built.
        # TODO: when the rule registry is added, exit rules should be built dynamically
        # from the strategy JSON rather than hardcoded here.
        self.exit_rules = [ATRStopLossRule()]

    def run(self):
        for bar in self.params.bars:
            self.state.update_drawdown(bar["close"], self.params.pair)

            if self.state.in_position:
                for rule in self.exit_rules:
                    reason = rule.evaluate(bar, self.state)
                    if reason:
                        # TODO: in a real system, exit price should be the next bar's open
                        # or the stop loss level itself (slippage modelling). Using close for now.
                        self.state.close_position(
                            pair=self.params.pair,
                            date=bar["timestamp"],
                            price=self.state.stop_loss,
                            reason=reason
                        )
                        break
            else:
                atr = bar.get("atr")
                if atr is None or (isinstance(atr, float) and math.isnan(atr)):
                    continue

                if self.entry_rule.evaluate(bar):
                    stop_loss = bar["close"] - (atr * self.params.atr_multiplier)
                    # TODO: in a real system, entry should be at the next bar's open, not
                    # the current bar's close. Using close for now to keep MVP simple.
                    self.state.open_position(
                        pair=self.params.pair,
                        date=bar["timestamp"],
                        price=bar["close"],
                        stop_loss=stop_loss
                    )
