# src/executor_ext.py
from executor import Executor

class SafeExecutor(Executor):
    def __init__(self, *args, min_order_usd=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_order_usd = min_order_usd

    def get_base_asset(self, symbol):
        return symbol.split('/')[0]

    def get_quote_asset(self, symbol):
        return symbol.split('/')[1]

    def get_balance_quote(self, symbol):
        q = self.get_quote_asset(symbol)
        bal = self.fetch_balance()
        return bal.get(q, 0)

    def safe_market_buy(self, symbol, usd_amount):
        if usd_amount < self.min_order_usd:
            raise ValueError(f"Order too small (min ${self.min_order_usd})")
        ticker = self.exchange.fetch_ticker(symbol)
        price = ticker.get('last') or ticker.get('close')
        if price is None:
            raise RuntimeError("Failed to fetch ticker price")
        qty = usd_amount / price
        qty = self._adjust_amount_by_step(symbol, qty)
        if qty <= 0:
            raise ValueError('Calculated qty <= 0 after step adjustment')
        return self.create_market_buy(symbol, qty)

    def safe_market_sell_all(self, symbol):
        base = self.get_base_asset(symbol)
        bal = self.fetch_balance()
        qty = bal.get(base, 0)
        if qty <= 0:
            raise ValueError('No base asset to sell')
        qty = self._adjust_amount_by_step(symbol, qty)
        return self.create_market_sell(symbol, qty)
