# src/app.py
import streamlit as st
from executor import Executor
from backtest import simple_backtest
import pandas as pd
from strategy_enhanced import compute_signals_enhanced
from utils import ensure_data_dirs
from report import save_trades_csv, save_equity_curve, plot_equity

ensure_data_dirs()
st.set_page_config(page_title='Binance Spot Bot', layout='wide')
st.title('Binance Spot Trading Bot — Backtest & Paper')

symbol = st.sidebar.text_input('Symbol', value='BTC/USDT')
timeframe = st.sidebar.text_input('Timeframe', value='1h')
fast = st.sidebar.number_input('EMA fast', value=9)
slow = st.sidebar.number_input('EMA slow', value=21)
rsi_period = st.sidebar.number_input('RSI period', value=14)
risk_per_trade = st.sidebar.slider('Risk per trade', 0.001, 0.2, 0.01)

ex = Executor(use_testnet=True)

if st.sidebar.button('Fetch balance'):
    st.sidebar.write(ex.fetch_balance())

if st.sidebar.button('Run backtest'):
    df = ex.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=500)
    res = simple_backtest(df, initial_cash=10000, risk_per_trade=risk_per_trade,
                          fast=fast, slow=slow, rsi_period=rsi_period)
    st.write('Final equity:', round(res['final_equity'],2))
    st.write('Max drawdown:', res['max_drawdown'])
    st.line_chart(pd.Series(res['equity_curve']))
    tpath = save_trades_csv(res['trades'], path='data/reports/backtest_trades.csv')
    epath = save_equity_curve(res['equity_curve'], path='data/reports/backtest_equity.csv')
    plot_equity(res['equity_curve'], path='data/reports/backtest_equity.png')
    st.success(f'Trades saved: {tpath}, equity saved: {epath}')

# Simple paper control (manual)
if 'paper' not in st.session_state:
    st.session_state['paper'] = False

if st.sidebar.button('Start paper trading'):
    st.session_state['paper'] = True
    st.info('Paper trading started (manual mode)')

if st.sidebar.button('Stop paper trading'):
    st.session_state['paper'] = False
    st.info('Paper trading stopped')

if st.session_state.get('paper'):
    st.write('Paper trading (manual tick) — fetching latest bar and suggesting order...')
    df = ex.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=50)
    sigs = compute_signals_enhanced(df, fast=fast, slow=slow, rsi_period=rsi_period)
    last_sig = sigs.iloc[-1]
    st.write(last_sig[['ts','close','ema_fast','ema_slow','rsi','signal']])
    if last_sig['signal_change'] == 1:
        st.write('Signal: BUY (suggested)')
    elif last_sig['signal_change'] == -1:
        st.write('Signal: SELL (suggested)')
