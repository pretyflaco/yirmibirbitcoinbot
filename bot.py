import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
from config import TELEGRAM_BOT_TOKEN, BTCTURK_API_TICKER_URL

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    update.message.reply_text(
        "Welcome! 👋 I can help you convert Turkish Lira to Bitcoin satoshi.\n\n"
        "Available commands:\n"
        "/100lira - Convert 100 TRY to satoshi using the current exchange rate\n"
        "/help - Show help message"
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message when the command /help is issued."""
    update.message.reply_text(
        "I can help you convert Turkish Lira to Bitcoin satoshi.\n\n"
        "Available commands:\n"
        "/100lira - Convert 100 TRY to satoshi using the current exchange rate"
    )

def convert_100lira(update: Update, context: CallbackContext) -> None:
    """Convert 100 TRY to satoshi and send the result."""
    try:
        # Fetch current exchange rate from BTCTurk
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        # Find the BTCTRY pair
        btc_try_data = None
        for pair_data in data.get('data', []):
            if pair_data.get('pair') == 'BTCTRY':
                btc_try_data = pair_data
                break
        
        if not btc_try_data:
            logger.error("BTCTRY pair not found in the API response")
            update.message.reply_text(
                "Sorry, I couldn't find the BTC/TRY exchange rate. Please try again later."
            )
            return
        
        # Extract the last price
        btc_try_rate = float(btc_try_data.get('last', 0))
        
        if btc_try_rate <= 0:
            logger.error(f"Invalid exchange rate: {btc_try_rate}")
            update.message.reply_text(
                "Sorry, I received an invalid exchange rate. Please try again later."
            )
            return
        
        # Calculate satoshi equivalent (1 BTC = 100,000,000 satoshi)
        lira_amount = 100
        btc_amount = lira_amount / btc_try_rate
        satoshi_amount = btc_amount * 100000000  # Convert BTC to satoshi
        
        # Format the response
        message = (
            f"💰 *100 Turkish Lira = {satoshi_amount:.0f} satoshi*\n\n"
            f"Exchange rate: 1 BTC = {btc_try_rate:,.2f} TRY\n"
            f"Data source: BTCTurk\n"
            f"_Updated just now_"
        )
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except requests.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        update.message.reply_text(
            "Sorry, I couldn't connect to the exchange. Please try again later."
        )
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data processing error: {str(e)}")
        update.message.reply_text(
            "Sorry, I encountered an error while processing the exchange data. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        update.message.reply_text(
            "An unexpected error occurred. Please try again later."
        )

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("100lira", convert_100lira))

    # Start the Bot
    logger.info("Starting bot...")
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
