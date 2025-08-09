# src/backtest.py
import pandas as pd
from strategy_enhanced import compute_signals_enhanced

def simple_backtest(df, initial_cash=10000, risk_per_trade=0.01,
                    fast=9, slow=21, rsi_period=14, rsi_buy=40, rsi_sell=60, min_volume=None):
    df2 = compute_signals_enhanced(df, fast=fast, slow=slow, rsi_period=rsi_period,
                                   rsi_buy_threshold=rsi_buy, rsi_sell_threshold=rsi_sell, min_volume=min_volume)
    cash = initial_cash
    position = 0.0
    equity_curve = []
    trades = []

    for i, row in df2.iterrows():
        price = row['close']
        sig_change = row['signal_change']
        if sig_change == 1 and position == 0:
            usd_to_risk = cash * risk_per_trade
            qty = usd_to_risk / price
            position = qty
            cash -= qty * price
            trades.append({'type':'buy','price':price,'qty':qty,'index':i})
        elif sig_change == -1 and position > 0:
            cash += position * price
            trades.append({'type':'sell','price':price,'qty':position,'index':i})
            position = 0

        equity_curve.append(cash + position * price)

    final = cash + position * df2.iloc[-1]['close']
    cummax = pd.Series(equity_curve).cummax()
    max_dd = ((pd.Series(equity_curve) - cummax) / cummax).min()
    return {
        'final_equity': final,
        'equity_curve': equity_curve,
        'trades': trades,
        'max_drawdown': max_dd,
    }
