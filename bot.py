#!/usr/bin/env python
# Python Telegram Bot - Direct implementation without ApplicationBuilder

import os
import logging
import asyncio
import pytz
import requests
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Import API configuration
from config import TELEGRAM_BOT_TOKEN, BTCTURK_API_TICKER_URL

# Define command handlers
async def start_command(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        "Merhaba! 👋 Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir\n"
        "/help - Yardım mesajını göster"
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message when the command /help is issued."""
    await update.message.reply_text(
        "Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir"
    )

async def convert_100lira_command(update: Update, context: CallbackContext) -> None:
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
            await update.message.reply_text(
                "Üzgünüm, BTC/TRY kurunu bulamadım. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        # Extract the last price
        btc_try_rate = float(btc_try_data.get('last', 0))
        
        if btc_try_rate <= 0:
            logger.error(f"Invalid exchange rate: {btc_try_rate}")
            await update.message.reply_text(
                "Üzgünüm, geçersiz bir kur aldım. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        # Calculate satoshi equivalent (1 BTC = 100,000,000 satoshi)
        lira_amount = 100
        btc_amount = lira_amount / btc_try_rate
        satoshi_amount = btc_amount * 100000000  # Convert BTC to satoshi
        
        # Format the response
        message = (
            f"💰 *100 Türk Lirası = {satoshi_amount:.0f} satoshi*\n\n"
            f"Kur: 1 BTC = {btc_try_rate:,.2f} TL\n"
            f"Veri kaynağı: BTCTurk\n"
            f"_Şu anda güncellendi_"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except requests.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, borsaya bağlanamadım. Lütfen daha sonra tekrar deneyin."
        )
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data processing error: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, borsa verilerini işlerken bir hata ile karşılaştım. Lütfen daha sonra tekrar deneyin."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        await update.message.reply_text(
            "Beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

# Simple polling mechanism
async def poll_updates(bot: Bot, handlers: dict):
    """Custom polling function to avoid ApplicationBuilder."""
    offset = 0
    while True:
        try:
            # Get updates from Telegram
            updates = await bot.get_updates(offset=offset, timeout=30)
            
            for update in updates:
                offset = update.update_id + 1
                
                # Process update with appropriate handler
                if update.message and update.message.text:
                    text = update.message.text
                    
                    # Check for commands
                    if text.startswith('/'):
                        command = text.split(' ')[0].lower()
                        if command in handlers:
                            await handlers[command](update, None)
                            logger.info(f"Handled command: {command}")
                        else:
                            logger.info(f"Unknown command: {command}")
                
                # Process the next update
                await asyncio.sleep(0.1)
            
            # Short delay before next polling
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error in polling: {e}")
            await asyncio.sleep(5)  # Wait a bit longer on error

async def main():
    """Set up and run the bot."""
    # Initialize the bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Set up command handlers
    handlers = {
        '/start': start_command,
        '/help': help_command,
        '/100lira': convert_100lira_command
    }
    
    # Test bot token before starting
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot initialized: @{bot_info.username}")
        
        # Start polling for updates
        logger.info("Starting bot polling...")
        await poll_updates(bot, handlers)
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        
if __name__ == '__main__':
    # Set timezone for Python runtime
    os.environ['TZ'] = 'UTC'
    
    # Run the main function
    asyncio.run(main())
