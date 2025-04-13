import os

# Telegram Bot Token - Get from environment variable with fallback to the provided token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7762709630:AAGZZ24dEZCS-Tm4pmZbToVM2esESzGEA3c")

# BTCTurk API URLs
BTCTURK_API_BASE_URL = "https://api.btcturk.com"
BTCTURK_API_TICKER_URL = f"{BTCTURK_API_BASE_URL}/api/v2/ticker"
