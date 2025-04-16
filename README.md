# Telegram Bitcoin Converter Bot

A Telegram bot that provides Bitcoin price information, currency conversion, and Satoshi Nakamoto quotes. All responses are in Turkish.

## Features

- Convert Turkish Lira (TRY) to Bitcoin satoshi
- Display current BTC/USD and BTC/TRY prices from multiple exchanges
- Show top volume trading pairs
- Display USDT/TRY and USD/TRY exchange rates
- Share Satoshi Nakamoto quotes in groups
- Lightning Network payments (admin only)
- Handles errors gracefully
- Includes a Flask web application for status monitoring
- All responses are in Turkish language

## Bot Commands

- `/start` - Start the bot and see available commands
- `/help` - Show help message
- `/100lira` - Convert 100 TRY to satoshi
- `/price` - Show current BTC/USD and BTC/TRY prices
- `/volume` - Show top 5 currency pairs with highest volume
- `/dollar` - Show USDT/TRY and USD/TRY exchange rates

Admin commands:
- `/ban [username]` - Ban a user from using the bot
- `/groupid` - Get the ID of the current chat
- `/gimmecheese` - Send Bitcoin via Lightning Network (admin only)

## Usage

You can use the bot on Telegram by searching for `@100liratosatoshi_bot` or clicking this link: [https://t.me/100liratosatoshi_bot](https://t.me/100liratosatoshi_bot)

Just send the command `/100lira` and the bot will reply with the current satoshi value of 100 TRY.

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (obtained from [@BotFather](https://t.me/BotFather))
- Blink API Key (optional, for Lightning Network payments)

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TelegramBitcoinConverter.git
   cd TelegramBitcoinConverter
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   BLINK_API_KEY=your_blink_api_key_here
   ADMIN_USERNAME=your_admin_username_here
   ```

4. Run the Telegram bot:
   ```bash
   python bot.py
   ```

5. In a separate terminal, run the web application (optional):
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```
   or
   ```bash
   python main.py
   ```

## Project Structure

```
TelegramBitcoinConverter/
├── README.md
├── requirements.txt
├── main.py
├── config.py
├── bot.py
├── api/
│   ├── __init__.py
│   ├── base.py
│   ├── blink.py
│   ├── btcturk.py
│   └── exchanges.py
├── handlers/
│   ├── __init__.py
│   ├── command_handlers.py
│   ├── conversation_handlers.py
│   └── message_handlers.py
├── utils/
│   ├── __init__.py
│   ├── rate_limiting.py
│   ├── quotes.py
│   └── formatting.py
├── quotes.json
└── quotes_tr.json
```

- `bot.py` - Main Telegram bot implementation
- `config.py` - Configuration settings for the bot and API
- `main.py` - Flask web application for status monitoring
- `api/` - API client modules for different exchanges
- `handlers/` - Command and message handler modules
- `utils/` - Utility modules for formatting, rate limiting, etc.
- `quotes.json` - Satoshi Nakamoto quotes in English
- `quotes_tr.json` - Satoshi Nakamoto quotes in Turkish

## Technical Details

- Integrates with multiple cryptocurrency exchanges to provide accurate price information
- Uses the BTCTurk API to get current BTC/TRY exchange rates and volume data
- Integrates with Blink API for Bitcoin price data and Lightning Network payments
- Fetches USD/TRY exchange rates from Yadio API
- Calculates the satoshi equivalent by dividing 100 TRY by the BTC/TRY rate and multiplying by 100,000,000
- Built with Python using python-telegram-bot library (v22.0)
- Implements rate limiting to prevent abuse
- Shares Satoshi Nakamoto quotes in tracked groups
- Responses are formatted in Turkish language
- Includes a Flask web application for monitoring the bot status
- Modular architecture for better maintainability and extensibility

## Running with Docker

If you prefer using Docker:

1. Create a Dockerfile:
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY . .

   RUN pip install -r requirements.txt

   CMD ["python", "bot.py"]
   ```

2. Build and run the Docker container:
   ```bash
   docker build -t telegram-bitcoin-converter .
   docker run -e TELEGRAM_BOT_TOKEN=your_bot_token_here \
              -e BLINK_API_KEY=your_blink_api_key_here \
              -e ADMIN_USERNAME=your_admin_username_here \
              telegram-bitcoin-converter
   ```

## Deployment

The bot can be deployed on various platforms:

### Replit

1. Fork this repository to your Replit account
2. Set the environment variables in Replit's Secrets tab
3. Set up the workflows to run the bot and web application

### Heroku

1. Create a new Heroku app
2. Connect your GitHub repository
3. Set the environment variables in the app settings
4. Deploy the app

### VPS/Dedicated Server

1. Clone the repository to your server
2. Install the dependencies
3. Create a systemd service to run the bot
4. Set up a reverse proxy with Nginx (optional)

## API Integrations

The bot integrates with multiple cryptocurrency exchanges to provide accurate price information:

- BTCTurk
- Binance
- Blink
- Bitfinex
- Bitstamp
- Coinbase
- Kraken
- Paribu
- OKX
- Bitflyer
- Yadio (for currency exchange rates)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
