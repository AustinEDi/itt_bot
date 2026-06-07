import pandas as pd
import yfinance as yf
import warnings
import logging

# Suppress yfinance 404 warnings (non‑critical, data still works)
warnings.filterwarnings('ignore', message='.*404.*')
logging.getLogger('yfinance').setLevel(logging.ERROR)

YAHOO_TICKER = '^DJI'

def get_candles(symbol, timeframe, limit=200):
    tf_map = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '60m',
        '4h': '60m',
        '1d': '1d'
    }
    if timeframe not in tf_map:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    yf_interval = tf_map[timeframe]
    ticker = yf.Ticker(YAHOO_TICKER)

    if timeframe == '4h':
        df = ticker.history(period='60d', interval='60m')
        df = df.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    else:
        df = ticker.history(period='max', interval=yf_interval)

    if df.empty:
        return pd.DataFrame(columns=['open','high','low','close','volume'])

    df.index.name = 'time'
    df = df.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low',
        'Close': 'close', 'Volume': 'volume'
    })
    df = df.tail(limit)
    return df[['open','high','low','close','volume']]
