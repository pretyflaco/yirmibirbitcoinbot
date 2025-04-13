import os
import sys
import re

# Telegram Bot Token - Get from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Validate token format (simple validation)
def is_valid_token_format(token):
    """Simple validation of Telegram bot token format."""
    if not token:
        return False
    # Basic format check (numbers:letters+numbers)
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token))

# Exit with error if the token is not set or invalid format
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
elif not is_valid_token_format(TELEGRAM_BOT_TOKEN):
    print("Error: The TELEGRAM_BOT_TOKEN format appears to be invalid.")
    print("A valid token typically looks like: 123456789:ABCDefGhIJklmNoPQRsTUVwxyZ")
    print("Please check your token and update it in the Secrets tab.")
    sys.exit(1)

# BTCTurk API URLs
BTCTURK_API_BASE_URL = "https://api.btcturk.com"
BTCTURK_API_TICKER_URL = f"{BTCTURK_API_BASE_URL}/api/v2/ticker"
