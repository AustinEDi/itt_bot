from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, Trade
from mt5.mt5_client import MT5Client
from strategy.itt_engine import analyze_market
from strategy.trade_manager import TradeManager
from ai.analyst import AIAnalyst
from data_provider import get_candles
import config
import threading
import time
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itt_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db.init_app(app)

bot_running = False
mt5 = None
ai = AIAnalyst()
trade_mgr = None
equity_snapshots = []
log_messages = []   # live activity log

def allowed_session():
    if not config.SESSION_TRADE:
        return True
    now = datetime.datetime.now(datetime.timezone.utc)
    hour_minute = now.hour + now.minute / 60.0
    for start, end in config.SESSION_HOURS:
        if start <= hour_minute < end:
            return True
    return False

def bot_loop():
    global bot_running, mt5, ai, trade_mgr, equity_snapshots, log_messages
    while bot_running:
        try:
            if not allowed_session():
                time.sleep(60)
                continue

            def log(msg):
                ts = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
                log_messages.append(f"[{ts}] {msg}")
                if len(log_messages) > 50:
                    log_messages.pop(0)

            log("🔄 Fetching account info...")
            info = mt5.get_account_info()
            equity_snapshots.append({
                'time': time.time(),
                'balance': info['balance'],
                'equity': info.get('equity', info['balance']),
                'profit': info.get('profit', 0)
            })
            if len(equity_snapshots) > 500:
                equity_snapshots.pop(0)

            log(f"📡 Fetching {config.TIMEFRAME_STRUCTURE} candles...")
            df_h1 = get_candles(config.SYMBOL, config.TIMEFRAME_STRUCTURE, config.CANDLE_LIMIT)
            log(f"   H1 candles: {len(df_h1)} rows, last close: {df_h1['close'].iloc[-1]:.2f}")

            log(f"📡 Fetching {config.TIMEFRAME_ENTRY} candles...")
            df_m5 = get_candles(config.SYMBOL, config.TIMEFRAME_ENTRY, config.CANDLE_LIMIT)
            log(f"   M5 candles: {len(df_m5)} rows, last close: {df_m5['close'].iloc[-1]:.2f}")

            if df_h1.empty or df_m5.empty:
                log("⚠️ Empty candle data, skipping...")
                time.sleep(30)
                continue

            log("🔍 Running ITT analysis...")
            signal = analyze_market(df_h1, df_m5)
            if signal['signal'] != 'NONE' and signal['features']:
                prob = ai.predict_proba(signal['features'])
                log(f"   Signal: {signal['signal']} | AI confidence: {prob:.2f} (threshold: {config.AI_CONFIDENCE_THRESHOLD})")
                if prob >= config.AI_CONFIDENCE_THRESHOLD:
                    log(f"✅ Trade triggered! Direction: {signal['direction']}, Entry: {signal['entry_price']}, SL: {signal['stop_loss']}, TP: {signal['take_profit']}")
                    trade_mgr = TradeManager(mt5, ai)
                    trade_mgr.open_trade(signal)
                else:
                    log(f"❌ AI filter blocked trade (confidence too low)")
            else:
                log("   No valid setup detected")

            time.sleep(60)
        except Exception as e:
            log(f"❌ Bot error: {e}")
            time.sleep(10)

# ---------- Routes ----------
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/api/start', methods=['POST'])
def start_bot():
    global bot_running, mt5, trade_mgr
    if bot_running:
        return jsonify({'status': 'already running'})
    try:
        if mt5 is None:
            login = int(os.getenv('MT5_LOGIN'))
            password = os.getenv('MT5_PASSWORD')
            server = os.getenv('MT5_SERVER')
            mt5 = MT5Client(config.METAAPI_TOKEN, os.getenv('METAAPI_ACCOUNT_ID'))
            mt5.start()
        trade_mgr = TradeManager(mt5, ai)
        bot_running = True
        threading.Thread(target=bot_loop, daemon=True).start()
        return jsonify({'status': 'started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global bot_running
    bot_running = False
    return jsonify({'status': 'stopping'})

@app.route('/api/status', methods=['GET'])
def status():
    balance = None
    if mt5:
        try:
            balance = mt5.get_account_info()['balance']
        except:
            pass
    return jsonify({
        'bot_running': bot_running,
        'connected': mt5 is not None,
        'account_balance': balance,
        'symbol': config.SYMBOL
    })

@app.route('/api/equity', methods=['GET'])
def equity():
    return jsonify(equity_snapshots)

@app.route('/api/history', methods=['GET'])
def history():
    trades = Trade.query.order_by(Trade.timestamp.desc()).limit(20).all()
    result = []
    for t in trades:
        profit = None
        if t.exit_price:
            profit = round((t.exit_price - t.entry_price) if t.direction == 'buy' else (t.entry_price - t.exit_price), 2)
        result.append({
            'id': t.id,
            'timestamp': t.timestamp.isoformat(),
            'symbol': t.symbol,
            'direction': t.direction,
            'entry': t.entry_price,
            'exit': t.exit_price,
            'result': 'win' if t.result == 1 else 'loss' if t.result == 0 else 'open',
            'profit': profit
        })
    return jsonify(result)

@app.route('/api/log', methods=['GET'])
def get_log():
    return jsonify(log_messages[-30:])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)
