import time
import json
from config import SYMBOL, LOT_SIZE
from models import db, Trade

class TradeManager:
    def __init__(self, mt5_client, ai_analyst):
        self.client = mt5_client
        self.ai = ai_analyst
        self.active_trade = None

    def open_trade(self, signal):
        direction = signal['direction']
        sl = signal['stop_loss']
        tp = signal['take_profit']
        volume = self._calc_lot(sl, signal['entry_price'])
        order_id = self.client.place_order(SYMBOL, direction, volume, sl=sl, tp=tp)
        self.active_trade = {
            'order_id': order_id,
            'direction': direction,
            'entry': signal['entry_price'],
            'sl': sl,
            'tp': tp,
            'features': signal['features'],
            'timestamp': time.time()
        }
        return order_id

    def _calc_lot(self, sl, entry):
        try:
            acc = self.client.get_account_info()
            balance = acc['balance']
            risk = balance * 0.2
            stop_dist = abs(entry - sl)
            if stop_dist == 0:
                return LOT_SIZE
            lot = risk / (stop_dist * 1)   # US30 $1/point per lot
            return max(0.01, round(lot, 2))
        except:
            return LOT_SIZE

    def record_closed_trade(self, exit_price, result):
        if not self.active_trade:
            return
        trade = Trade(
            symbol=SYMBOL,
            direction=self.active_trade['direction'],
            entry_price=self.active_trade['entry'],
            exit_price=exit_price,
            result=1 if result == 'win' else 0,
            features_json=json.dumps(self.active_trade['features'])
        )
        db.session.add(trade)
        db.session.commit()
        self.active_trade = None
