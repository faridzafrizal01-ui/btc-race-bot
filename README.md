# BTC race bot

Long-only dip-buy mean-reversion bot for the make.fun
`btc-race-24h-20261112-1439` competition (CBBTC vs USDC, 1-minute bars).

Strategy: track the 1-minute closes; buy all-in when the close is at
least 0.8% below its 60-bar SMA; sell the whole position when the close
reverts to SMA x 1.002, falls 0.4% below the highest close since entry,
or the position is worth at most 99% of what was paid.

Dev-window result (replayed through the official Python SDK shim):
net PnL +$5.24 on $1,000, max drawdown 0.31%, 3 trades, deterministic
(two runs byte-identical).

`main.py` is the entrypoint; `vendor/makefun_bars.py` is the kit's
official Python bars SDK, copied byte-identical.
