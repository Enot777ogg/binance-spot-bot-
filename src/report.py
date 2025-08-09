# src/report.py
import pandas as pd
import matplotlib.pyplot as plt

def save_trades_csv(trades, path='data/reports/trades.csv'):
    df = pd.DataFrame(trades)
    df.to_csv(path, index=False)
    return path

def save_equity_curve(equity_curve, path='data/reports/equity.csv'):
    df = pd.DataFrame({'equity': equity_curve})
    df.to_csv(path, index=False)
    return path

def plot_equity(equity_curve, path='data/reports/equity.png'):
    plt.figure()
    plt.plot(equity_curve)
    plt.title('Equity curve')
    plt.xlabel('Step')
    plt.ylabel('Equity')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path
