import os
import sys

# Telegram Bot Token - Get from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Exit with error if the token is not set
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
    print("Please set the TELEGRAM_BOT_TOKEN environment variable with your Telegram bot token.")
    print("Example: export TELEGRAM_BOT_TOKEN='your_token_here'")
    sys.exit(1)

# BTCTurk API URLs
BTCTURK_API_BASE_URL = "https://api.btcturk.com"
BTCTURK_API_TICKER_URL = f"{BTCTURK_API_BASE_URL}/api/v2/ticker"
