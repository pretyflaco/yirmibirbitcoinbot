import os
import sys

# Telegram Bot Token - Get from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Exit with error if the token is not set
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
    print("\nTo set the token in Replit:")
    print("1. Click on the 'Secrets (Environment variables)' tab in the sidebar")
    print("2. Click 'Add new secret'")
    print("3. Key: TELEGRAM_BOT_TOKEN")
    print("4. Value: Your telegram token (without any quotes)")
    print("5. Click 'Add secret'")
    print("\nFor local development:")
    print("export TELEGRAM_BOT_TOKEN=your_token_here (without quotes)")
    sys.exit(1)

# BTCTurk API URLs
BTCTURK_API_BASE_URL = "https://api.btcturk.com"
BTCTURK_API_TICKER_URL = f"{BTCTURK_API_BASE_URL}/api/v2/ticker"
