from .indicators import *

def analyze_market(df_h1, df_m5):
    signal = "NONE"
    direction = entry = sl = tp = None
    features = {}

    profile = market_structure(df_h1)
    features['profile_bullish'] = 1 if profile == 'bullish' else 0
    features['profile_bearish'] = 1 if profile == 'bearish' else 0

    sh, sl = swing_points(df_h1)
    if sh.empty or sl.empty:
        return {"signal": "NONE"}

    buy_liq = sh['high'].iloc[-1]
    sell_liq = sl['low'].iloc[-1]

    fvg_bull, fvg_bear = fair_value_gaps(df_m5)
    curr = df_m5.iloc[-1]

    if profile == 'bullish':
        sweep = liquidity_sweep(df_m5, sell_liq, 'sell_side')
        if sweep:
            absorb = absorption(df_m5, 'bullish')
            ch = change_of_character(df_m5)
            disp = displacement(df_m5, sell_liq, 'bullish')
            fvg_entry = None
            if fvg_bull:
                low, high = fvg_bull[-1][1], fvg_bull[-1][2]
                if low <= curr['close'] <= high:
                    fvg_entry = (low + high) / 2
            if absorb and ch == 'bullish' and disp and fvg_entry:
                direction = 'buy'
                entry = curr['close']
                sl = sell_liq - 10
                tp = buy_liq
                signal = "BUY"
                features['sweep'] = 1
                features['absorption'] = 1
                features['choch_bull'] = 1
                features['displacement'] = 1
                features['fvg_distance'] = abs(entry - fvg_entry)

    elif profile == 'bearish':
        sweep = liquidity_sweep(df_m5, buy_liq, 'buy_side')
        if sweep:
            absorb = absorption(df_m5, 'bearish')
            ch = change_of_character(df_m5)
            disp = displacement(df_m5, buy_liq, 'bearish')
            fvg_entry = None
            if fvg_bear:
                high, low = fvg_bear[-1][1], fvg_bear[-1][2]
                if low <= curr['close'] <= high:
                    fvg_entry = (high + low) / 2
            if absorb and ch == 'bearish' and disp and fvg_entry:
                direction = 'sell'
                entry = curr['close']
                sl = buy_liq + 10
                tp = sell_liq
                signal = "SELL"
                features['sweep'] = 1
                features['absorption'] = 1
                features['choch_bear'] = 1
                features['displacement'] = 1
                features['fvg_distance'] = abs(entry - fvg_entry)

    return {
        "signal": signal,
        "direction": direction,
        "entry_price": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "features": features
    }
