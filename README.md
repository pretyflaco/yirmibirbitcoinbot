# TRY to Satoshi Telegram Bot

A Telegram bot that converts 100 Turkish Lira (TRY) to its Bitcoin satoshi equivalent using real-time exchange rates from BTCTurk.

## Features

- Responds to `/100lira` command with the satoshi equivalent of 100 Turkish Lira
- Fetches real-time exchange rates from BTCTurk API
- Properly calculates satoshi values (1 BTC = 100,000,000 satoshi)
- Handles errors gracefully
- Includes a Flask web application for status monitoring

## Bot Commands

- `/start` - Displays a welcome message and available commands
- `/help` - Shows help information
- `/100lira` - Converts 100 Turkish Lira to its satoshi equivalent

## Usage

You can use the bot on Telegram by searching for `@yirmibir21bot` or clicking this link: [https://t.me/yirmibir21bot](https://t.me/yirmibir21bot)

Just send the command `/100lira` and the bot will reply with the current satoshi value of 100 TRY.

## Technical Details

- Uses the BTCTurk API to get current BTC/TRY exchange rates
- API endpoint: https://api.btcturk.com/api/v2/ticker
- The bot extracts the BTCTRY pair data from the API response
- Calculates the satoshi equivalent by dividing 100 TRY by the BTC/TRY rate and multiplying by 100,000,000
- Built with Python using python-telegram-bot library (v13.7)
- Includes a Flask web application for status monitoring

## Installation and Setup

1. Install the required Python libraries:
   ```
   pip install python-telegram-bot==13.7 flask requests
   ```

2. Set the Telegram Bot token as an environment variable:
   ```
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   ```

3. Run the bot:
   ```
   python bot.py
   ```

4. Run the web application:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## Error Handling

The bot handles various error scenarios:
- Network/API connection issues
- Invalid or missing data in API responses
- Data parsing errors

## Deployment

The bot is deployed on Replit and runs 24/7.
