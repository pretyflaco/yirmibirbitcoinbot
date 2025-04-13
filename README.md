# TRY to Satoshi Telegram Bot

A Telegram bot that converts 100 Turkish Lira (TRY) to its Bitcoin satoshi equivalent using real-time exchange rates from BTCTurk. All responses are in Turkish.

## Features

- Responds to `/100lira` command with the satoshi equivalent of 100 Turkish Lira
- Fetches real-time exchange rates from BTCTurk API
- Properly calculates satoshi values (1 BTC = 100,000,000 satoshi)
- Handles errors gracefully
- Includes a Flask web application for status monitoring
- All responses are in Turkish language

## Bot Commands

- `/start` - Displays a welcome message and available commands
- `/help` - Shows help information
- `/100lira` - Converts 100 Turkish Lira to its satoshi equivalent

## Usage

You can use the bot on Telegram by searching for `@yirmibir21bot` or clicking this link: [https://t.me/yirmibir21bot](https://t.me/yirmibir21bot)

Just send the command `/100lira` and the bot will reply with the current satoshi value of 100 TRY.

## Installation and Setup

### Prerequisites

- Python 3.6 or higher
- Telegram Bot Token (obtained from [@BotFather](https://t.me/BotFather))

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/try-to-satoshi-bot.git
   cd try-to-satoshi-bot
   ```

2. Install the required dependencies:
   ```bash
   pip install -r packages.txt
   ```
   
   or manually install:
   ```bash
   pip install python-telegram-bot==13.7 requests flask gunicorn
   ```

3. Create a `config.py` file or modify the existing one:
   ```python
   import os
   
   # Telegram Bot Token
   TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token_here")
   
   # BTCTurk API URLs
   BTCTURK_API_BASE_URL = "https://api.btcturk.com"
   BTCTURK_API_TICKER_URL = f"{BTCTURK_API_BASE_URL}/api/v2/ticker"
   ```

4. Set your Telegram Bot Token as an environment variable:

   **In Replit:**
   - Click on the "Secrets (Environment variables)" tab in the sidebar
   - Click "Add new secret"
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: Your Telegram bot token (paste it without any quotes)
   - Click "Add secret"

   **On your local machine:**
   ```bash
   export TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```
   Note: Do not use quotes around your token when setting the environment variable

5. Run the Telegram bot:
   ```bash
   python bot.py
   ```
   
6. In a separate terminal, run the web application:
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```
   or
   ```bash
   python main.py
   ```

## Project Structure

- `bot.py` - Main Telegram bot implementation
- `config.py` - Configuration settings for the bot and API
- `main.py` - Flask web application for status monitoring
- `LICENSE` - MIT License
- `packages.txt` - Required Python packages

## Technical Details

- Uses the BTCTurk API to get current BTC/TRY exchange rates
- API endpoint: https://api.btcturk.com/api/v2/ticker
- The bot extracts the BTCTRY pair data from the API response
- Calculates the satoshi equivalent by dividing 100 TRY by the BTC/TRY rate and multiplying by 100,000,000
- Built with Python using python-telegram-bot library (v13.7)
- Responses are formatted in Turkish language
- Includes a Flask web application for monitoring the bot status

## Running with Docker

If you prefer using Docker:

1. Create a Dockerfile:
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY . .
   
   RUN pip install -r packages.txt
   
   CMD ["python", "bot.py"]
   ```

2. Build and run the Docker container:
   ```bash
   docker build -t try-to-satoshi-bot .
   docker run -e TELEGRAM_BOT_TOKEN=your_bot_token_here try-to-satoshi-bot
   ```
   Note: Do not use quotes around your token in the docker run command

## Deployment

The bot is deployed on Replit and runs 24/7. To deploy to Replit:

1. Fork this repository to your Replit account
2. Set the Telegram bot token in Replit's secrets
3. Set up the workflows to run the bot and web application

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
