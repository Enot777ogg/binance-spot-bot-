# src/app_live.py
import streamlit as st
import time
import threading
from executor_ext import SafeExecutor
from strategy_enhanced import compute_signals_enhanced
from report import save_trades_csv, save_equity_curve, plot_equity
from utils import ensure_data_dirs

ensure_data_dirs()
st.set_page_config(page_title='Paper Trading — Live', layout='wide')
st.title('Paper Trading — Binance Testnet (Start/Stop)')

symbol = st.sidebar.text_input('Symbol', value='BTC/USDT')
timeframe = st.sidebar.text_input('Timeframe', value='1h')
fast = st.sidebar.number_input('EMA fast', value=9, min_value=2)
slow = st.sidebar.number_input('EMA slow', value=21, min_value=3)
rsi_buy = st.sidebar.number_input('RSI buy threshold', value=40, min_value=1, max_value=99)
rsi_sell = st.sidebar.number_input('RSI sell threshold', value=60, min_value=1, max_value=99)
min_volume = st.sidebar.number_input('Min volume (optional, set 0 to disable)', value=0.0)
initial_cash = st.sidebar.number_input('Initial cash (USD) — used for sizing', value=10000.0)
risk_per_trade = st.sidebar.slider('Risk per trade', 0.001, 0.2, 0.01)
min_order_usd = st.sidebar.number_input('Min order USD (safety)', value=10.0)

if 'worker' not in st.session_state:
    st.session_state['worker'] = None
    st.session_state['running'] = False
    st.session_state['log'] = []
    st.session_state['equity'] = []
    st.session_state['trades'] = []

ex = SafeExecutor(use_testnet=True, min_order_usd=min_order_usd)

class Worker(threading.Thread):
    def __init__(self, ex, symbol, timeframe, params):
        super().__init__()
        self.ex = ex
        self.symbol = symbol
        self.timeframe = timeframe
        self.params = params
        self._stop_event = threading.Event()
        self.in_position = False

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        cash = self.params.get('initial_cash', 10000)
        while not self.stopped():
            try:
                df = self.ex.fetch_ohlcv(symbol=self.symbol, timeframe=self.timeframe, limit=200)
                df2 = compute_signals_enhanced(
                    df,
                    fast=self.params['fast'],
                    slow=self.params['slow'],
                    rsi_period=14,
                    rsi_buy_threshold=self.params['rsi_buy'],
                    rsi_sell_threshold=self.params['rsi_sell'],
                    min_volume=(self.params['min_volume'] or None)
                )
                last = df2.iloc[-1]
                prev = df2.iloc[-2]
                st.session_state['log'].append(f"{time.ctime()}: last_signal={last['signal']}")

                # enter
                if prev['signal'] <= 0 and last['signal'] == 1 and not self.in_position:
                    usd_to_risk = cash * self.params['risk_per_trade']
                    try:
                        order = self.ex.safe_market_buy(self.symbol, usd_to_risk)
                        self.in_position = True
                        st.session_state['trades'].append({'type':'buy','price': order.get('price', None),'info': order})
                        st.session_state['log'].append(f"Bought for ${usd_to_risk}")
                    except Exception as e:
                        st.session_state['log'].append(f"Buy error: {e}")

                # exit
                if prev['signal'] >= 0 and last['signal'] == -1 and self.in_position:
                    try:
                        order = self.ex.safe_market_sell_all(self.symbol)
                        self.in_position = False
                        st.session_state['trades'].append({'type':'sell','price': order.get('price', None),'info': order})
                        st.session_state['log'].append('Sold all base')
                    except Exception as e:
                        st.session_state['log'].append(f"Sell error: {e}")

                # update equity simple estimate
                balance = self.ex.fetch_balance()
                quote = self.ex.get_quote_asset(self.symbol)
                quote_bal = balance.get(quote, 0)
                base = self.ex.get_base_asset(self.symbol)
                base_bal = balance.get(base, 0)
                last_price = df2.iloc[-1]['close']
                total_value = quote_bal + base_bal * last_price
                st.session_state['equity'].append(total_value)

            except Exception as e:
                st.session_state['log'].append(f"Worker exception: {e}")

            time.sleep(10)

col1, col2 = st.columns([1,3])
with col1:
    if st.button('Start paper trading') and not st.session_state['running']:
        params = {
            'fast': fast, 'slow': slow,
            'rsi_buy': rsi_buy, 'rsi_sell': rsi_sell,
            'min_volume': (min_volume or None),
            'initial_cash': initial_cash, 'risk_per_trade': risk_per_trade
        }
        worker = Worker(ex, symbol, timeframe, params)
        st.session_state['worker'] = worker
        st.session_state['running'] = True
        worker.start()
        st.success('Worker started (paper trading)')

    if st.button('Stop paper trading') and st.session_state['running']:
        worker = st.session_state.get('worker')
        if worker:
            worker.stop()
            worker.join(timeout=5)
        st.session_state['running'] = False
        st.success('Worker stopped')

with col2:
    st.subheader('Logs')
    st.write('\n'.join(st.session_state['log'][-200:]))

st.subheader('Trades (last 50)')
st.write(st.session_state['trades'][-50:])

st.subheader('Equity chart')
st.line_chart(st.session_state['equity'][-500:])

if st.button('Save report'):
    tpath = save_trades_csv(st.session_state['trades'], path='data/reports/trades_report.csv')
    epath = save_equity_curve(st.session_state['equity'], path='data/reports/equity_report.csv')
    img = plot_equity(st.session_state['equity'], path='data/reports/equity_report.png')
    st.success(f'Reports saved: {tpath}, {epath}, {img}')

st.markdown('---')
st.write('Use Start/Stop carefully. This runs on Binance Testnet sandbox when USE_TESTNET=true in .env.')
