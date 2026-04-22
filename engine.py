import pandas as pd
import numpy as np

def run_backtest(data: list, take_profit_pct: float, stop_loss_pct: float):
    """
    Core deterministic backtesting engine.
    In production, 'data' would be years of CSV OHLCV data.
    """
    # Convert incoming JSON data into a high-speed Pandas DataFrame
    df = pd.DataFrame(data)
    
    # Calculate a simple 20-period rolling high (Resistance)
    df['rolling_high'] = df['close'].rolling(window=20).max().shift(1)
    
    initial_capital = 100000
    capital = initial_capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = []

    for index, row in df.iterrows():
        # 1. Check for Buy Signal (Price breaks out above recent resistance)
        if position == 0 and not pd.isna(row['rolling_high']) and row['close'] > row['rolling_high']:
            position = 1
            entry_price = row['close']
            trades.append({"type": "BUY", "price": entry_price, "time": row['time']})
            
        # 2. Check for Sell Signal (Hit Take Profit or Stop Loss)
        elif position == 1:
            profit_target = entry_price * (1 + take_profit_pct)
            stop_loss = entry_price * (1 - stop_loss_pct)
            
            if row['high'] >= profit_target:
                capital += capital * take_profit_pct
                position = 0
                trades.append({"type": "SELL", "price": profit_target, "time": row['time'], "pnl": "WIN"})
            elif row['low'] <= stop_loss:
                capital -= capital * stop_loss_pct
                position = 0
                trades.append({"type": "SELL", "price": stop_loss, "time": row['time'], "pnl": "LOSS"})
        
        equity_curve.append({"time": row['time'], "equity": capital})

    # Calculate final metrics
    wins = len([t for t in trades if t.get("pnl") == "WIN"])
    total_closed_trades = len([t for t in trades if "pnl" in t])
    win_rate = (wins / total_closed_trades * 100) if total_closed_trades > 0 else 0
    
    return {
        "final_capital": round(capital, 2),
        "return_pct": round(((capital - initial_capital) / initial_capital) * 100, 2),
        "win_rate": round(win_rate, 2),
        "total_trades": total_closed_trades,
        "equity_curve": equity_curve,
        "trade_log": trades
    }