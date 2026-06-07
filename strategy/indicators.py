import pandas as pd
import numpy as np

def swing_points(df, window=5):
    highs = df['high'].rolling(window=window, center=True).max()
    lows = df['low'].rolling(window=window, center=True).min()
    sh = df[df['high'] == highs].copy()
    sl = df[df['low'] == lows].copy()
    return sh, sl

def market_structure(df, lookback=50):
    recent = df.iloc[-lookback:]
    sh, sl = swing_points(recent)
    if sh.empty or sl.empty:
        return "consolidating"
    if sh['high'].iloc[-1] > sh['high'].iloc[0] and sl['low'].iloc[-1] > sl['low'].iloc[0]:
        return "bullish"
    elif sh['high'].iloc[-1] < sh['high'].iloc[0] and sl['low'].iloc[-1] < sl['low'].iloc[0]:
        return "bearish"
    return "consolidating"

def fair_value_gaps(df):
    fvg_bull, fvg_bear = [], []
    for i in range(1, len(df)-1):
        prev = df.iloc[i-1]
        next_ = df.iloc[i+1]
        if prev['high'] < next_['low']:
            fvg_bull.append((i+1, prev['high'], next_['low']))
        elif prev['low'] > next_['high']:
            fvg_bear.append((i+1, prev['low'], next_['high']))
    return fvg_bull, fvg_bear

def liquidity_sweep(df, level, direction, lookback=5):
    recent = df.iloc[-lookback:]
    if direction == 'sell_side':
        return recent['low'].min() < level and recent['close'].iloc[-1] > level
    return recent['high'].max() > level and recent['close'].iloc[-1] < level

def displacement(df, level, direction, strength=1.5):
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    avg_body = (df['high'] - df['low']).rolling(20).mean().iloc[-1]
    if avg_body == 0:
        return False
    if direction == 'bullish':
        return last['close'] > level and body > strength * avg_body
    return last['close'] < level and body > strength * avg_body

def change_of_character(df):
    sh, sl = swing_points(df)
    if sh.empty or sl.empty:
        return None
    if df['close'].iloc[-1] > sh['high'].iloc[-1]:
        return 'bullish'
    elif df['close'].iloc[-1] < sl['low'].iloc[-1]:
        return 'bearish'
    return None

def absorption(df, direction):
    last = df.iloc[-1]
    if direction == 'bullish':
        lower_wick = min(last['open'], last['close']) - last['low']
        body = abs(last['close'] - last['open'])
        return lower_wick > body * 1.5 and last['close'] > last['open']
    else:
        upper_wick = last['high'] - max(last['open'], last['close'])
        body = abs(last['close'] - last['open'])
        return upper_wick > body * 1.5 and last['close'] < last['open']
