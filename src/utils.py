# src/utils.py
import os

def ensure_data_dirs():
    os.makedirs('data/reports', exist_ok=True)

def format_order_info(order):
    # helper to pretty-print order info
    if not order:
        return {}
    return {
        'id': order.get('id'),
        'status': order.get('status'),
        'filled': order.get('filled'),
        'price': order.get('price') or order.get('average'),
    }
