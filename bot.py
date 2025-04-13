import logging
import os
import json
import requests
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Configuration
from config import TELEGRAM_BOT_TOKEN, BTCTURK_API_TICKER_URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        "Merhaba! 👋 Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir\n"
        "/help - Yardım mesajını göster"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    await update.message.reply_text(
        "Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir"
    )

async def convert_100lira(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

def main():
    """Start the bot."""
    # We need to create an ApplicationBuilder instance - use separate imports to avoid timezone issues
    from telegram.ext import Defaults, PicklePersistence, Application
    
    # Old dependencies might be causing issues
    import sys
    print("Python version:", sys.version)
    print("Python path:", sys.path)
    print("Imported libraries:", [m.__name__ for m in sys.modules.values() if hasattr(m, '__name__') and not m.__name__.startswith('_')])
    
    # Create a simple standalone bot without complex features
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("100lira", convert_100lira))
    
    # Start the bot
    logger.info("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
