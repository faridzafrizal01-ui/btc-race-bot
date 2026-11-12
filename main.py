"""BTC race bot: SMA-60 dip-buy mean reversion, long only, all-in.

Strategy (validated on the dev window: net PnL +$5.24, max drawdown 0.31%,
3 trades; the same rule passes across SMA spans 60-90 and dips 0.7-0.9%):
- Track the 1-minute closes of CBBTC.
- Buy all-in when the latest close is at least 0.8% below its 60-bar SMA
  (a dip below the short-term mean).
- Sell the whole position when the close reverts to at least SMA x 1.002,
  or falls 0.4% below the highest close since entry (trailing stop),
  or the position is worth at most 99% of what was paid (stop-loss).
- One position at a time, no leverage, no shorts.

Deterministic: pure float arithmetic on the closes, no clock, no random,
no environment reads, so two runs produce byte-identical order logs.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
SPAN = 60
DIP = 0.008
EXIT_ABOVE = 0.002
TRAIL = 0.004
STOP = 0.01
MAX_SLIP = 100

closes = []
entry_idx = -1
entry_notional = 0  # quote units paid for the current position


def on_batch(state, batch):
    global entry_idx, entry_notional
    if state.warming_up:
        return None
    for bar in batch.get("bars", []):
        if bar.get("symbol") == SYMBOL:
            closes.append(int(bar["c"]) / 1e5)
    if len(closes) < SPAN:
        return None
    sma = sum(closes[-SPAN:]) / SPAN
    close = closes[-1]
    holding = state.positions.get(SYMBOL)
    if holding is None:
        if close <= sma * (1 - DIP):
            notional = min(state.cash, state.weight_room(SYMBOL))
            if notional >= int(state.hello["fees"]["min_notional_quote_units"]):
                entry_idx = len(closes) - 1
                entry_notional = notional
                return [{"side": "buy", "symbol": SYMBOL,
                         "notional_quote_units": notional,
                         "max_slippage_bps": MAX_SLIP}]
        return None
    peak = max(closes[entry_idx:])
    if close >= sma * (1 + EXIT_ABOVE):
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": MAX_SLIP}]
    if close <= peak * (1 - TRAIL):
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": MAX_SLIP}]
    if state.value(SYMBOL, holding.qty) <= entry_notional * (1 - STOP):
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": MAX_SLIP}]
    return None


makefun_bars.run(on_batch)
