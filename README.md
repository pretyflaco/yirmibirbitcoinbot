# TRY to Satoshi Telegram Bot

A Telegram bot that converts 100 Turkish Lira (TRY) to its Bitcoin satoshi equivalent using real-time exchange rates from BTCTurk.

## Features

- Responds to `/100lira` command with the satoshi equivalent of 100 Turkish Lira
- Fetches real-time exchange rates from BTCTurk API
- Properly calculates satoshi values (1 BTC = 100,000,000 satoshi)
- Handles errors gracefully

## Commands

- `/start` - Displays a welcome message and available commands
- `/help` - Shows help information
- `/100lira` - Converts 100 Turkish Lira to its satoshi equivalent

## Setup and Run

1. Install the required Python libraries:
   ```
   pip install python-telegram-bot requests
   ```

2. Set the Telegram Bot token as an environment variable (optional, falls back to the provided token):
   ```
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   ```

3. Run the bot:
   ```
   python bot.py
   ```

## Technical Details

- Uses the BTCTurk API to get current BTC/TRY exchange rates
- API endpoint: https://api.btcturk.com/api/v2/ticker
- The bot extracts the BTCTRY pair data from the API response
- Calculates the satoshi equivalent by dividing 100 TRY by the BTC/TRY rate and multiplying by 100,000,000

## Error Handling

The bot handles various error scenarios:
- Network/API connection issues
- Invalid or missing data in API responses
- Data parsing errors
