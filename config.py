"""Configuration settings for the Telegram Bitcoin Converter Bot.

This module contains all configuration settings, API endpoints, and environment variables
used throughout the application. It validates critical settings like the Telegram Bot Token
and provides helpful error messages if configuration is incorrect.

Environment Variables:
    TELEGRAM_BOT_TOKEN: The token for the Telegram Bot API
    BLINK_API_KEY: API key for the Blink API
    ADMIN_USERNAME: Username of the bot administrator

API Endpoints:
    Various API endpoints for cryptocurrency exchanges

GraphQL Queries:
    Predefined GraphQL queries for the Blink API
"""

import os
import sys
import re
import logging
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

# Telegram Bot Token - Get from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Admin username for special commands
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "pretyflaco")

# Rate limiting settings
PUBLIC_GROUP_COOLDOWN = int(os.getenv("PUBLIC_GROUP_COOLDOWN", "3600"))  # 1 hour in seconds
PRIVATE_CHAT_COOLDOWN = int(os.getenv("PRIVATE_CHAT_COOLDOWN", "900"))   # 15 minutes in seconds

# Quote posting settings
QUOTE_INTERVAL = int(os.getenv("QUOTE_INTERVAL", "86400"))  # 24 hours in seconds (1 day)
QUOTE_SOURCE_URL = "https://github.com/dergigi/QuotableSatoshi"

# RSS feed monitoring settings
RSS_FEED_URL = "https://anchor.fm/s/587d3d4c/podcast/rss"
RSS_CHECK_INTERVAL = int(os.getenv("RSS_CHECK_INTERVAL", "3600"))  # 1 hour in seconds

# Validate token format (simple validation)
def is_valid_token_format(token):
    """Simple validation of Telegram bot token format.

    Args:
        token (str): The Telegram bot token to validate

    Returns:
        bool: True if the token format is valid, False otherwise
    """
    if not token:
        return False
    # Basic format check (numbers:letters+numbers)
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token))

# Exit with error if the token is not set or invalid format
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
    print("\nTo set the token:")
    print("1. Create a .env file in the project root")
    print("2. Add the line: TELEGRAM_BOT_TOKEN=your_token_here (without quotes)")
    print("\nOr set it directly in your environment:")
    print("export TELEGRAM_BOT_TOKEN=your_token_here (without quotes)")
    sys.exit(1)
elif not is_valid_token_format(TELEGRAM_BOT_TOKEN):
    print("Error: The TELEGRAM_BOT_TOKEN format appears to be invalid.")
    print("A valid token typically looks like: 123456789:ABCDefGhIJklmNoPQRsTUVwxyZ")
    print("Please check your token and update it in your .env file or environment variables.")
    sys.exit(1)

# BTCTurk API URLs
BTCTURK_API_BASE_URL = "https://api.btcturk.com"
BTCTURK_API_TICKER_URL = "https://api.btcturk.com/api/v2/ticker"

# Blink API URLs and Queries
BLINK_API_URL = "https://api.blink.sv/graphql"
BLINK_API_KEY = os.getenv("BLINK_API_KEY", "")

# Blink GraphQL queries
BLINK_PRICE_QUERY = """
query BtcPriceList($first: Int!) {
  btcPriceList(first: $first) {
    price {
      base
      offset
    }
    timestamp
  }
}
"""

BLINK_PRICE_VARIABLES = {
    "first": 1
}

# Yadio API URL for currency exchange rates
YADIO_API_URL = "https://api.yadio.io/exrates/USD"

# Additional cryptocurrency exchange API URLs
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"
KRAKEN_API_URL = "https://api.kraken.com/0/public/Ticker"
PARIBU_API_URL = "https://www.paribu.com/ticker"
BITFINEX_API_URL = "https://api-pub.bitfinex.com/v2/ticker"
BITSTAMP_API_URL = "https://www.bitstamp.net/api/v2/ticker"
COINBASE_API_URL = "https://api.coinbase.com/v2/prices"
OKX_API_URL = "https://www.okx.com/api/v5/market/ticker"
BITFLYER_API_URL = "https://api.bitflyer.com/v1/ticker"

# LNBits API
LNBITS_API_URL = "https://lnbits.ideasarelikeflames.org/api/v1"
LNBITS_API_KEY = os.getenv("LNBITS_API_KEY", "")

# Check if LNBits API key is set
if not LNBITS_API_KEY:
    logger.warning("LNBITS_API_KEY environment variable is not set. /wallet command will not work.")
