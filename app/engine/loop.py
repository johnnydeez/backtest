import math
from app.engine.params import BacktestParams
from app.engine.state import TestState
from app.engine.rules.entry import BreakoutEntryRule
from app.engine.rules.exit import ATRStopLossRule, NDayLowTakeProfitRule, TimeoutRule


class BacktestLoop:
    """
    Iterates bar-by-bar over historical data and orchestrates entry/exit decisions.
    Delegates all decision logic to rule objects — contains no strategy logic itself.
    """

    def __init__(self, params: BacktestParams, state: TestState):
        self.params = params
        self.state = state
        self.entry_rule = BreakoutEntryRule()
        self.exit_rules = self._build_exit_rules()

    def _build_exit_rules(self):
        exit_config = self.params.strategy.get("rules", {}).get("exit", {})
        rules = []
        if "stop_loss" in exit_config:
            rules.append(ATRStopLossRule())
        if "take_profit" in exit_config:
            rules.append(NDayLowTakeProfitRule(exit_config["take_profit"]))
        if "timeout" in exit_config:
            rules.append(TimeoutRule(exit_config["timeout"]))
        return rules

    def run(self):
        for bar in self.params.bars:
            self.state.update_drawdown(bar["timestamp"], bar["close"], self.params.pair)

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
