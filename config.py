import os
from dotenv import load_dotenv

load_dotenv()

METAAPI_TOKEN = os.getenv("METAAPI_TOKEN")
if not METAAPI_TOKEN:
    raise RuntimeError("METAAPI_TOKEN not set in .env")

SYMBOL = os.getenv("SYMBOL", "US30m")
TIMEFRAME_STRUCTURE = os.getenv("TIMEFRAME_STRUCTURE", "1h")
TIMEFRAME_ENTRY = os.getenv("TIMEFRAME_ENTRY", "5m")
CANDLE_LIMIT = int(os.getenv("CANDLE_LIMIT", 200))
LOT_SIZE = float(os.getenv("LOT_SIZE", 0.01))
MAX_DAILY_LOSS_PERCENT = float(os.getenv("MAX_DAILY_LOSS_PERCENT", 30.0))
AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", 0.65))
SESSION_TRADE = os.getenv("SESSION_TRADE", "true").lower() in ("true", "1", "yes")
SESSION_HOURS_STR = os.getenv("SESSION_HOURS", "13-17")

def _parse_hours(env_str):
    pairs = []
    for part in env_str.split(","):
        if "-" in part:
            start_str, end_str = part.split("-")
            try:
                start = float(start_str.strip())
                end = float(end_str.strip())
            except:
                start = int(start_str.strip())
                end = int(end_str.strip())
            pairs.append((start, end))
    return pairs

SESSION_HOURS = _parse_hours(SESSION_HOURS_STR)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
