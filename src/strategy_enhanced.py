# src/strategy_enhanced.py
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

def compute_signals_enhanced(df, fast=9, slow=21, rsi_period=14,
                             rsi_buy_threshold=40, rsi_sell_threshold=60,
                             min_volume=None):
    df = df.copy()
    if 'close' not in df.columns:
        raise ValueError("DataFrame must contain 'close' column")
    df['ema_fast'] = EMAIndicator(df['close'], window=fast).ema_indicator()
    df['ema_slow'] = EMAIndicator(df['close'], window=slow).ema_indicator()
    df['rsi'] = RSIIndicator(df['close'], window=rsi_period).rsi()

    df['signal'] = 0
    cond_long = (df['ema_fast'] > df['ema_slow']) & (df['rsi'] > rsi_buy_threshold)
    cond_exit = (df['ema_fast'] < df['ema_slow']) | (df['rsi'] > rsi_sell_threshold)

    if min_volume is not None and 'vol' in df.columns:
        cond_long = cond_long & (df['vol'] >= min_volume)

    df.loc[cond_long, 'signal'] = 1
    df.loc[cond_exit, 'signal'] = -1
    df['signal_change'] = df['signal'].diff().fillna(0)
    return df
