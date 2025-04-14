#!/usr/bin/env python
# Python Telegram Bot Implementation with v22.0

import os
import logging
import asyncio
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import API configuration
from config import (
    TELEGRAM_BOT_TOKEN, 
    BTCTURK_API_TICKER_URL,
    BLINK_API_URL,
    BLINK_PRICE_QUERY,
    BLINK_PRICE_VARIABLES
)

# Yadio API URL
YADIO_API_URL = "https://api.yadio.io/exrates/USD"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        "Merhaba! 👋 Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir\n"
        "/price - Güncel BTC/USD ve BTC/TRY kurlarını göster\n"
        "/volume - En yüksek hacimli 5 para birimi çiftini göster\n"
        "/dollar - USDT/TRY ve USD/TRY kurlarını göster\n"
        "/help - Yardım mesajını göster"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    await update.message.reply_text(
        "Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir\n"
        "/price - Güncel BTC/USD ve BTC/TRY kurlarını göster\n"
        "/volume - En yüksek hacimli 5 para birimi çiftini göster\n"
        "/dollar - USDT/TRY ve USD/TRY kurlarını göster"
    )

async def get_btc_usd_price():
    """Fetch current BTC/USD price from Blink API."""
    try:
        response = requests.post(
            BLINK_API_URL,
            json={
                "query": BLINK_PRICE_QUERY,
                "variables": BLINK_PRICE_VARIABLES
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and 'btcPriceList' in data['data'] and data['data']['btcPriceList']:
            # Get the most recent price (last item in the array)
            price_data = data['data']['btcPriceList'][-1]['price']
            base = float(price_data['base'])
            offset = int(price_data['offset'])
            # Fix the 10x multiplier issue by dividing by 100
            return (base / (10 ** offset)) / 100
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price: {str(e)}")
        return None

async def get_btc_try_price():
    """Fetch current BTC/TRY price from BTCTurk API."""
    try:
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for pair_data in data.get('data', []):
            if pair_data.get('pair') == 'BTCTRY':
                return float(pair_data.get('last', 0))
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/TRY price: {str(e)}")
        return None

async def get_top_volume_pairs():
    """Fetch top 5 currency pairs with highest volume from BTCTurk API."""
    try:
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            # Sort pairs by volume in descending order
            sorted_pairs = sorted(
                data['data'], 
                key=lambda x: float(x.get('volume', 0)), 
                reverse=True
            )
            
            # Get top 5 pairs
            top_pairs = sorted_pairs[:5]
            
            return top_pairs
        
        return None
    except Exception as e:
        logger.error(f"Error fetching top volume pairs: {str(e)}")
        return None

async def get_usdt_try_rate():
    """Fetch USDT/TRY rate from BTCTurk API."""
    try:
        logger.info("Fetching USDT/TRY rate from BTCTurk API...")
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"BTCTurk API response: {data}")
        
        for pair_data in data.get('data', []):
            if pair_data.get('pair') == 'USDTTRY':
                rate = float(pair_data.get('last', 0))
                logger.info(f"Found USDT/TRY rate: {rate}")
                return rate
        
        logger.error("USDTTRY pair not found in BTCTurk API response")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching USDT/TRY rate: {str(e)}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data processing error fetching USDT/TRY rate: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching USDT/TRY rate: {str(e)}")
        return None

async def get_usd_try_rate():
    """Fetch USD/TRY rate from Yadio API."""
    try:
        logger.info("Fetching USD/TRY rate from Yadio API...")
        response = requests.get(YADIO_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Yadio API response: {data}")
        
        if 'TRY' in data:
            rate = float(data['TRY'])
            logger.info(f"Found USD/TRY rate: {rate}")
            return rate
        
        logger.error("TRY rate not found in Yadio API response")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching USD/TRY rate: {str(e)}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data processing error fetching USD/TRY rate: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching USD/TRY rate: {str(e)}")
        return None

async def volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show top 5 currency pairs with highest volume."""
    try:
        top_pairs = await get_top_volume_pairs()
        
        if not top_pairs:
            await update.message.reply_text(
                "Üzgünüm, hacim bilgilerini alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        message = "📊 *En Yüksek Hacimli 5 Para Birimi Çifti*\n\n"
        
        for i, pair in enumerate(top_pairs, 1):
            pair_name = pair.get('pair', '')
            volume = float(pair.get('volume', 0))
            denominator_symbol = pair.get('denominatorSymbol', '')
            
            message += f"{i}. *{pair_name}*: {volume:,.2f} {denominator_symbol}\n"
        
        message += "\n_Veri kaynağı: BTCTurk_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in volume command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def dollar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show USDT/TRY and USD/TRY exchange rates."""
    try:
        usdt_try_rate = await get_usdt_try_rate()
        usd_try_rate = await get_usd_try_rate()
        
        if usdt_try_rate is None or usd_try_rate is None:
            await update.message.reply_text(
                "Üzgünüm, döviz kurlarını alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        message = (
            f"💵 *Güncel Dolar Kurları*\n\n"
            f"*USDT/TRY:* ₺{usdt_try_rate:.2f}\n"
            f"*USD/TRY:* ₺{usd_try_rate:.2f}\n\n"
            f"_Veri kaynakları: BTCTurk, Yadio_"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in dollar command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current BTC/USD and BTC/TRY prices."""
    try:
        btc_usd_price = await get_btc_usd_price()
        btc_try_price = await get_btc_try_price()
        
        if btc_usd_price is None or btc_try_price is None:
            await update.message.reply_text(
                "Üzgünüm, fiyat bilgilerini alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        message = (
            f"💰 *Güncel Bitcoin Fiyatları*\n\n"
            f"*BTC/USD:* ${int(btc_usd_price):,}\n"
            f"*BTC/TRY:* ₺{int(btc_try_price):,}\n\n"
            f"_Veri kaynakları: Blink API, BTCTurk_"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in price command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
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
            f"Kur: 1 BTC = ₺{int(btc_try_rate):,}\n"
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

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("100lira", convert_100lira))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("volume", volume_command))
    application.add_handler(CommandHandler("dollar", dollar_command))

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
