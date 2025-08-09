# src/executor.py
import ccxt
import os
from dotenv import load_dotenv
import math
import pandas as pd

load_dotenv()

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
USE_TESTNET = os.getenv('USE_TESTNET', 'true').lower() in ('1','true','yes')

EXCHANGE_ID = 'binance'

class Executor:
    def __init__(self, api_key=None, api_secret=None, use_testnet=True):
        self.api_key = api_key or API_KEY
        self.api_secret = api_secret or API_SECRET
        self.use_testnet = use_testnet
        self.exchange = getattr(ccxt, EXCHANGE_ID)({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })
        try:
            # ccxt exposes sandbox for binance in some builds
            if self.use_testnet and 'set_sandbox_mode' in dir(self.exchange):
                self.exchange.set_sandbox_mode(True)
        except Exception as e:
            print('Sandbox mode not set:', e)

    def fetch_ohlcv(self, symbol='BTC/USDT', timeframe='1h', limit=500):
        bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['ts','open','high','low','close','vol'])
        df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        return df

    def fetch_balance(self):
        return self.exchange.fetch_free_balance()

    def _adjust_amount_by_step(self, symbol, amount):
        try:
            markets = self.exchange.load_markets()
            m = markets.get(symbol)
            if m and 'limits' in m and m['limits'].get('amount'):
                step = m['limits']['amount'].get('step')
                if step:
                    precision = int(round(-math.log10(step))) if step < 1 else 0
                    return math.floor(amount * (10**precision)) / (10**precision)
        except Exception:
            pass
        return amount

    def create_market_buy(self, symbol, amount):
        amount = self._adjust_amount_by_step(symbol, amount)
        return self.exchange.create_market_buy_order(symbol, amount)

    def create_market_sell(self, symbol, amount):
        amount = self._adjust_amount_by_step(symbol, amount)
        return self.exchange.create_market_sell_order(symbol, amount)
