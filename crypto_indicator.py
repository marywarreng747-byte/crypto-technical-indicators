






























import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import argparse
from datetime import datetime

def fetch_ohlcv(exchange, symbol, timeframe='1h', limit=500):
    """Fetch OHLCV data from exchange."""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def calculate_indicators(df):
    """Add technical indicators using pandas_ta."""
    # Trend indicators
    df['ema_9'] = ta.ema(df['close'], length=9)
    df['ema_21'] = ta.ema(df['close'], length=21)
    df['sma_50'] = ta.sma(df['close'], length=50)
    
    # Momentum
    df['rsi'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)
    
    # Volatility
    bb = ta.bbands(df['close'], length=20)
    df = pd.concat([df, bb], axis=1)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    
    # Stochastic
    stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
    df = pd.concat([df, stoch], axis=1)
    
    return df

def generate_signals(df):
    """Simple example strategy: RSI + MACD crossover."""
    df['signal'] = 0
    
    # Buy signal: RSI < 30 (oversold) and MACD line crosses above signal
    buy_condition = (
        (df['rsi'] < 30) &
        (df['MACD_12_26_9'] > df['MACDs_12_26_9']) &
        (df['MACD_12_26_9'].shift(1) <= df['MACDs_12_26_9'].shift(1))
    )
    
    # Sell signal: RSI > 70 (overbought) and MACD line crosses below signal
    sell_condition = (
        (df['rsi'] > 70) &
        (df['MACD_12_26_9'] < df['MACDs_12_26_9']) &
        (df['MACD_12_26_9'].shift(1) >= df['MACDs_12_26_9'].shift(1))
    )
    
    df.loc[buy_condition, 'signal'] = 1   # Buy
    df.loc[sell_condition, 'signal'] = -1 # Sell
    
    return df

def plot_indicators(df, symbol, timeframe):
    """Interactive plot with candlestick + indicators."""
    fig = make_subplots(rows=4, cols=1, 
                        shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.4, 0.2, 0.2, 0.2],
                        subplot_titles=(f"{symbol} {timeframe} Chart", "RSI", "MACD", "Stochastic"))
    
    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['open'], high=df['high'],
                                 low=df['low'], close=df['close'],
                                 name='Price'), row=1, col=1)
    
    # EMAs
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_9'], name='EMA 9', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_21'], name='EMA 21', line=dict(color='blue')), row=1, col=1)
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], name='BB Lower', line=dict(color='gray')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], name='BB Upper', line=dict(color='gray')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACDs_12_26_9'], name='Signal', line=dict(color='orange')), row=3, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], name='Histogram'), row=3, col=1)
    
    # Stochastic
    fig.add_trace(go.Scatter(x=df.index, y=df['STOCHk_14_3_3'], name='%K', line=dict(color='blue')), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['STOCHd_14_3_3'], name='%D', line=dict(color='red')), row=4, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="green", row=4, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color="red", row=4, col=1)
    
    fig.update_layout(height=900, title_text=f"Crypto Technical Indicators - {symbol} ({timeframe})",
                      xaxis_rangeslider_visible=False)
    fig.show()

def main():
    parser = argparse.ArgumentParser(description="Crypto Technical Indicator Script")
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading pair (default: BTC/USDT)')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe (e.g., 15m, 1h, 4h, 1d)')
    parser.add_argument('--limit', type=int, default=500, help='Number of candles')
    args = parser.parse_args()

    # Initialize exchange (Binance - no API key needed for public data)
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })

    print(f"Fetching data for {args.symbol} on {args.timeframe}...")
    df = fetch_ohlcv(exchange, args.symbol, args.timeframe, args.limit)
    
    df = calculate_indicators(df)
    df = generate_signals(df)
    
    print(f"\nLatest data for {args.symbol}:")
    print(df.tail(5)[['close', 'rsi', 'MACD_12_26_9', 'signal']])
    
    # Show recent signals
    signals = df[df['signal'] != 0].tail(5)
    if not signals.empty:
        print("\nRecent Signals:")
        print(signals[['close', 'rsi', 'signal']])
    
    plot_indicators(df, args.symbol, args.timeframe)

if __name__ == "__main__":
    main()
