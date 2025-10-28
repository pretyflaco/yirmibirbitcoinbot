# Yirmibir Bitcoin Telegram Bot

A Telegram bot that provides Bitcoin price information, currency conversion, and Satoshi Nakamoto quotes. All responses are in Turkish.

## Features

- Convert Turkish Lira (TRY) to Bitcoin satoshi
- Display current BTC/USD and BTC/TRY prices from multiple exchanges
- Show top volume trading pairs
- Display USDT/TRY and USD/TRY exchange rates
- **Automatically post new YouTube videos** from [@yirmibirbitcoin channel](https://www.youtube.com/@yirmibirbitcoin)
- **Monitor Yirmibir Bitcoin Podcast** RSS feed for new episodes
- Share Satoshi Nakamoto quotes in groups (every 24 hours)
- Lightning Network payments (admin only)
- LNBits wallet integration
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

## Automated Content Posting

The bot automatically monitors and posts new content to tracked Telegram groups:

### YouTube Videos
- **Channel**: [@yirmibirbitcoin](https://www.youtube.com/@yirmibirbitcoin)
- **Check Frequency**: Every 30 minutes
- **Format**: 🎬 *Yeni Video:* [Title] + [Link]

### Podcast Episodes
- **Source**: [Yirmibir Bitcoin Podcast RSS Feed](https://anchor.fm/s/587d3d4c/podcast/rss)
- **Check Frequency**: Every hour
- **Format**: 🎙️ *Yeni Bölüm:* [Title] + [Link]

### Satoshi Quotes
- **Source**: Turkish translations of Satoshi Nakamoto quotes
- **Frequency**: Every 24 hours
- **Format**: 💭 *Satoshi Nakamoto'dan bir alıntı:* [Quote]

For more details, see [YOUTUBE_MONITORING.md](YOUTUBE_MONITORING.md)

## Usage

You can use the bot on Telegram by searching for `@yirmibir21bot` or clicking this link: [https://t.me/yirmibir21bot](https://t.me/yirmibir21bot)

The bot provides multiple commands including `/100lira` to convert 100 TRY to satoshi, `/price` to check current Bitcoin prices, and more. All responses are in Turkish.

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (obtained from [@BotFather](https://t.me/BotFather))
- Blink API Key (optional, for Lightning Network payments)

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/pretyflaco/yirmibirbitcoinbot.git
   cd yirmibirbitcoinbot
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
   
   # Optional: Customize check intervals (in seconds)
   QUOTE_INTERVAL=86400           # Satoshi quotes (24 hours)
   RSS_CHECK_INTERVAL=3600        # Podcast RSS feed (1 hour)
   YOUTUBE_CHECK_INTERVAL=1800    # YouTube videos (30 minutes)
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
yirmibirbitcoinbot/
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
│   ├── rss_monitor.py
│   ├── youtube_monitor.py
│   └── formatting.py
├── database/
│   ├── __init__.py
│   └── db.py
├── quotes.json
├── quotes_tr.json
└── YOUTUBE_MONITORING.md
```

- `bot.py` - Main Telegram bot implementation
- `config.py` - Configuration settings for the bot and API
- `main.py` - Flask web application for status monitoring
- `api/` - API client modules for different exchanges
- `handlers/` - Command and message handler modules
- `utils/` - Utility modules for formatting, rate limiting, quotes, RSS/YouTube monitoring
- `database/` - Database management for LNBits wallets
- `quotes.json` - Satoshi Nakamoto quotes in English
- `quotes_tr.json` - Satoshi Nakamoto quotes in Turkish
- `YOUTUBE_MONITORING.md` - Documentation for YouTube monitoring feature

## Technical Details

- Integrates with multiple cryptocurrency exchanges to provide accurate price information
- Uses the BTCTurk API to get current BTC/TRY exchange rates and volume data
- Integrates with Blink API for Bitcoin price data and Lightning Network payments
- **Monitors YouTube RSS feeds** to automatically detect and post new videos
- **Monitors podcast RSS feeds** for new episode notifications
- Fetches USD/TRY exchange rates from Yadio API
- Calculates the satoshi equivalent by dividing 100 TRY by the BTC/TRY rate and multiplying by 100,000,000
- Built with Python using python-telegram-bot library (v22.0)
- Implements rate limiting to prevent abuse
- Automated content posting (YouTube videos, podcast episodes, Satoshi quotes)
- LNBits wallet integration with SQLite database
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
   docker build -t yirmibirbitcoinbot .
   docker run -e TELEGRAM_BOT_TOKEN=your_bot_token_here \
              -e BLINK_API_KEY=your_blink_api_key_here \
              -e ADMIN_USERNAME=your_admin_username_here \
              yirmibirbitcoinbot
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
