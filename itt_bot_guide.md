# ITT US30 Trading Bot – Complete Documentation

**Version:** 1.0  
**Date:** June 2026  
**Platform:** Android (Termux) + MetaApi Cloud

---

## 1. Overview

The **ITT US30 Bot** is a fully automated trading system that implements **Institutional Transaction Theory (ITT)** on the US30 index. It runs on an Android phone via **Termux**, using **MetaApi Cloud** to connect to a MetaTrader 5 account. A built‑in **Random Forest AI** filters trade signals, and a **web dashboard** provides real‑time monitoring.

### Key Features
- Complete ITT analysis (liquidity sweeps, CHOCH, FVG, displacement, absorption)
- Multi‑timeframe (1H for structure, 5M for entry)
- Pure‑NumPy Random Forest AI (self‑learning)
- Automatic risk management (2% per trade)
- NY AM session filter (13:30–16:30 UTC - 08:30-11:30 EST)
- Equity curve, trade history, and live status dashboard
- Runs 24/7 on Android with Termux

---

## 2. System Architecture

[Android Phone] → Web Browser (http://localhost:5000)

                |
        Flask Backend (app.py)
                |
┌───────────────┼───────────────┐
|               |               |
ITT Engine   AI Analyst    MetaApi Client (SDK)
|                               |
Trade Manager             MetaApi Cloud → MT5 Broker


- **Flask** serves the dashboard and controls the bot.
- **MetaApi Cloud** bridges the bot to your MT5 account.
- **ITT Engine** analyzes price action and generates trade signals.
- **AI Analyst** (Random Forest) filters signals based on historical win/loss patterns.
- **Trade Manager** calculates lot size and places market orders with SL/TP.

---

## 3. Trading Strategy (ITT)

The bot follows a strict **Institutional Transaction Theory** model on US30.

### 3.1 Market Profile (1H)
- Determine overall structure: **Bullish**, **Bearish**, or **Consolidating**.
- Higher Highs + Higher Lows → Bullish.
- Lower Highs + Lower Lows → Bearish.
- No clear direction → Consolidating.

### 3.2 Liquidity Identification
- **Swing Highs / Lows** – where stop losses and breakout orders accumulate.
- **Equal Highs / Lows** – concentrated liquidity pools.
- **Fair Value Gaps (FVG)** – price imbalances that often get rebalanced.
- **Order Blocks** – areas of institutional activity.

### 3.3 Liquidity Events
- **Liquidity Sweep:** price moves beyond a level, triggers stops, then reverses.
- **Absorption:** repeated wick rejection indicating institutional order filling.
- **Change of Character (CHOCH):** market structure shift after a liquidity grab.
- **Displacement:** strong close beyond a swing point with momentum.

### 3.4 Entry Models

#### ✅ Buy Model
1. Bullish overall structure.
2. Sweep below a previous swing low (sell‑side liquidity).
3. Bullish absorption (lower wick rejection).
4. Bullish CHOCH (breaks bearish structure).
5. Bullish displacement.
6. Retracement into a bullish Fair Value Gap (FVG).
7. Target: next swing high (buy‑side liquidity).

#### ❌ Sell Model (mirrored for bearish conditions)

### 3.5 Indicator Parameters
|       Parameter            |     Value     |        Description            |
|----------------------------|---------------|-------------------------------|
| Swing window               | 5 candles     | Local maxima/minima detection |
| Market structure lookback  | 50 candles    | Trend determination           |
| Displacement strength      | 1.5× avg body | Minimum body/range ratio      |
| Absorption wick/body ratio | 1.5×          | Wick vs candle body           |
| Sweep lookback             | 5 candles     | Recent sweep detection        |

All parameters are adjustable in `strategy/indicators.py`.

---

## 4. AI Analyst (Machine Learning Filter)

### 4.1 Model Architecture
- **Type:** Random Forest classifier (pure NumPy, no scikit‑learn).
- **Trees:** 50
- **Max depth per tree:** 5
- **Min samples per split:** 5
- **Training trigger:** After every **10 closed trades**.
- **Input features (8):**
  - `profile_bullish`, `profile_bearish`
  - `sweep`, `absorption`
  - `choch_bull`, `choch_bear`
  - `displacement`
  - `fvg_distance`

### 4.2 Workflow
1. For each ITT signal, features are extracted.
2. Random Forest predicts the **probability of a winning trade**.
3. Trade is executed only if probability ≥ `AI_CONFIDENCE_THRESHOLD` (default 0.65).
4. After every 10 new closed trades, model retrains on full history.

The trained model is saved in `model.pkl`.

---

## 5. Trade Management & Risk

### 5.1 Lot Size Calculation
Risk per trade = **2% of account balance**.

lot_size = (balance × 0.02) / (stop_distance × 1)


- US30 assumed value: **$1 per point per lot**.
- Minimum lot: 0.01.

### 5.2 Stop Loss & Take Profit
- **SL:** placed 10 points below/above the swept swing level.
- **TP:** set to the opposite liquidity pool (next swing high/low).

### 5.3 Trade Recording
Completed trades are stored in `itt_bot.db` with entry/exit price, direction, result, and feature vector. This data feeds the AI retraining.

---

## 6. Session Filter

The bot trades **only during the New York AM session**:

| Timezone | Hours         |
|----------|---------------|
| EST      | 08:30 – 11:30 |
| UTC      | 13:30 – 16:30 |

Session boundaries are defined in `.env` (`SESSION_HOURS=13.5-16.5`). The check uses UTC hour + minute fraction. Outside these hours, the bot sleeps.

---

## 7. Dashboard & Monitoring

The dashboard is a single‑page web app (HTML + Tailwind CSS + Chart.js). It provides:

- **Status indicator** (Running / Stopped with pulsing green dot)
- **Account balance**
- **Floating P&L** (from account profit)
- **Win rate** (from trade history)
- **Equity curve** (balance over time, line chart)
- **Trade history table** (last 10 trades)
- **Start / Stop buttons**

Data refreshes automatically every 5 seconds.

---

## 8. File Structure


~/itt_bot/
├── .env                    # Credentials and settings
├── requirements.txt        # Python dependencies
├── app.py                  # Flask server & bot control
├── models.py               # Database models (Trade)
├── config.py               # Loads settings from .env
├── strategy/
│   ├── indicators.py       # Technical indicators
│   ├── itt_engine.py       # ITT signal generation
│   └── trade_manager.py    # Order placement & risk
├── ai/
│   └── analyst.py          # Pure‑NumPy Random Forest
├── mt5/
│   └── mt5_client.py       # MetaApi SDK client (DNS patched)
├── frontend/
│   └── index.html          # Dashboard UI
├── account_id.txt          # Saved MetaApi account ID (auto‑created)
└── model.pkl               # Trained AI model (auto‑created)



---

## 9. Configuration (.env)

All settings are in the `.env` file. **Replace placeholders with your real data.**

MetaApi Connection

METAAPI_TOKEN=your_metaapi_api_token
METAAPI_ACCOUNT_ID=abc123...            # from MetaApi cloud after manual account creation

MT5 Account

MT5_LOGIN=12345678
MT5_PASSWORD=your_mt5_password
MT5_SERVER=Exness-MT5Real10

Trading Parameters

SYMBOL=US30
TIMEFRAME_STRUCTURE=1h
TIMEFRAME_ENTRY=5m
CANDLE_LIMIT=200

Risk & AI

LOT_SIZE=0.01
MAX_DAILY_LOSS_PERCENT=2.0
AI_CONFIDENCE_THRESHOLD=0.65

Session Filter (UTC)

SESSION_TRADE=true
SESSION_HOURS=13.5-16.5     # NY AM session

Security

SECRET_KEY=your_random_secret_key       # generate with: python3 -c "import secrets; print(secrets.token_hex(32))"


---

## 10. Installation & Setup (Android/Termux)

### 10.1 Install Termux
Get Termux from **F‑Droid** (not Google Play).  
Update packages:
```bash
pkg update && pkg upgrade

10.2 Install Python & Build Tools

```bash
pkg install python clang build-essential openblas binutils
```

10.3 Create Project Directory & Copy Files

```bash
mkdir ~/itt_bot && cd ~/itt_bot
```

Copy all source files into this directory (use the provided archive or create each file manually).

10.4 Install Python Dependencies

```bash
pip install -r requirements.txt
```

10.5 Configure .env

Edit .env with your real credentials.

10.6 Add MT5 Account to MetaApi Cloud

· Go to app.metaapi.cloud
· Click Add Account → MetaTrader 5
· Enter your MT5 login, password, server
· Select Cloud as account type
· After creation, Copy the Account ID
· Paste it into .env as METAAPI_ACCOUNT_ID=...

10.7 Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Put the output in .env as SECRET_KEY.

10.8 (Optional) DNS Fix

If your network blocks MetaApi domains, create Termux DNS config:

```bash
echo "nameserver 8.8.8.8" > ~/.termux/resolv.conf
echo "nameserver 1.1.1.1" >> ~/.termux/resolv.conf
termux-reload-settings
```

11. Health Check & First Run

Before starting the bot, test the connection:

```bash
cd ~/itt_bot
python3 -c "
import os; from dotenv import load_dotenv; load_dotenv(dotenv_path='.env')
from mt5.mt5_client import MT5Client; import config
client = MT5Client(config.METAAPI_TOKEN, os.getenv('METAAPI_ACCOUNT_ID'))
client.start()
print('Balance:', client.get_account_info()['balance'])
"
```

If you see your account balance, everything is wired correctly.

---

12. Running the Bot

Start the Flask server:

```bash
cd ~/itt_bot
python app.py
```

Open your phone’s browser to http://localhost:5000.
Tap Start to begin trading.

The bot will:

· Connect to MetaApi
· Wait for the NY AM session
· Fetch candles and run ITT analysis every minute
· Execute trades when all ITT conditions + AI filter pass
· Record equity snapshots and completed trades

To stop, tap Stop on the dashboard.

Symptom Possible Cause Solution
"No running event loop" Async not properly configured Ensure you are using the latest mt5/mt5_client.py from the provided source.
"Timeout connecting to MetaApi" DNS/network issue Apply the Termux DNS fix (Section 10.8) or use a VPN.
"Validation failed … 400 Bad Request" Duplicate MetaApi account creation Use manual account creation in MetaApi web dashboard and provide the account ID.
Bot does not place any trades Session filter, strict ITT conditions, or AI threshold too high Check current UTC time; lower AI_CONFIDENCE_THRESHOLD (e.g., 0.55); verify market is moving.
AI not learning Not enough closed trades recorded AI retrains after 10 completed trades. Ensure trades are being closed (SL/TP hit).

14. FAQ

Q: Can I run the bot without Termux?
A: Yes, any Python 3.8+ environment with the required dependencies works (Windows, Linux, macOS). Termux is only needed for Android.

Q: Does the bot work on a real account?
A: It is designed for both demo and live accounts. Always test extensively on demo first.

Q: How do I change the trading session?
A: Edit SESSION_HOURS in .env (UTC format, supports multiple windows, e.g., 13.5-16.5,8-12).

Q: Can I trade a different symbol?
A: Change SYMBOL in .env (e.g., NAS100, SPX500). Ensure your broker provides the symbol.

Q: How do I reset the AI?
A: Delete model.pkl – the bot will start learning from scratch.

Q: How do I get a MetaApi token?
A: Register at metaapi.cloud and copy your API token from the dashboard.

Q: What is the minimum Android version?
A: Termux requires Android 7.0 (API 24) or higher.

---

End of document




