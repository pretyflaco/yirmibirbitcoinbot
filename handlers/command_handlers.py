"""Command handlers for the Telegram bot.

This module contains handler functions for the bot's commands.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Union

from telegram import Update
from telegram.ext import ContextTypes

from api.btcturk import BTCTurkAPI
from api.blink import BlinkAPI
from api.exchanges import ExchangesAPI
from utils.rate_limiting import is_banned, check_rate_limit, ban_user
from utils.quotes import get_random_quote
from utils.formatting import (
    format_price_message,
    format_volume_message,
    format_dollar_message,
    format_100lira_message
)
from config import ADMIN_USERNAME

# Set up logging
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "start"):
        return
    
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
    """Send a help message when the command /help is issued.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "help"):
        return
    
    # Check if user is admin
    is_admin = update.effective_user.username == ADMIN_USERNAME
    
    help_text = (
        "Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir\n"
        "/price - Güncel BTC/USD ve BTC/TRY kurlarını göster\n"
        "/volume - En yüksek hacimli 5 para birimi çiftini göster\n"
        "/dollar - USDT/TRY ve USD/TRY kurlarını göster"
    )
    
    # Add admin commands if user is admin
    if is_admin:
        help_text += "\n\nAdmin komutları:\n/ban [kullanıcı_adı] - Kullanıcıyı banla\n/groupid - Mevcut sohbetin ID'sini göster"
    
    await update.message.reply_text(help_text)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from using the bot.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Only admin can use this command
    if update.effective_user.username != ADMIN_USERNAME:
        return
    
    # Check if username is provided
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Kullanım: /ban [kullanıcı_adı]")
        return
    
    username = context.args[0].strip('@')
    
    # Don't allow banning the admin
    if username == ADMIN_USERNAME:
        await update.message.reply_text("Kendinizi banlayamazsınız.")
        return
    
    # Add user to banned list
    if ban_user(username):
        await update.message.reply_text(f"@{username} kullanıcısı banlandı.")
    else:
        await update.message.reply_text(f"@{username} kullanıcısı zaten banlanmış.")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current BTC/USD and BTC/TRY prices from multiple sources.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "price"):
        return
    
    try:
        # Send an initial message to indicate that we're fetching prices
        await update.message.reply_text("Bitcoin fiyatları alınıyor, lütfen bekleyin...")
        
        # Fetch BTC/TRY prices from all sources
        btcturk_btc_try = await BTCTurkAPI.get_btc_try_price()
        binance_btc_try = await ExchangesAPI.get_binance_btc_try_price()
        bitfinex_btc_try = await ExchangesAPI.get_bitfinex_btc_try_price()
        paribu_btc_try = await ExchangesAPI.get_paribu_btc_try_price()
        
        # Fetch BTC/USD prices from all sources
        blink_btc_usd = await BlinkAPI.get_btc_usd_price()
        btcturk_btc_usd = await BTCTurkAPI.get_btc_usd_price()
        binance_btc_usd = await ExchangesAPI.get_binance_btc_usd_price()
        kraken_btc_usd = await ExchangesAPI.get_kraken_btc_usd_price()
        paribu_btc_usd = await ExchangesAPI.get_paribu_btc_usd_price()
        bitfinex_btc_usd = await ExchangesAPI.get_bitfinex_btc_usd_price()
        bitstamp_btc_usd = await ExchangesAPI.get_bitstamp_btc_usd_price()
        coinbase_btc_usd = await ExchangesAPI.get_coinbase_btc_usd_price()
        okx_btc_usd = await ExchangesAPI.get_okx_btc_usd_price()
        bitflyer_btc_usd = await ExchangesAPI.get_bitflyer_btc_usd_price()
        
        # Organize prices into dictionaries
        btc_try_prices = {
            "BTCTurk": btcturk_btc_try,
            "Binance": binance_btc_try,
            "Bitfinex": bitfinex_btc_try,
            "Paribu": paribu_btc_try
        }
        
        btc_usd_prices = {
            "BTCTurk": btcturk_btc_usd,
            "Binance": binance_btc_usd,
            "Blink": blink_btc_usd,
            "Bitstamp": bitstamp_btc_usd,
            "Bitfinex": bitfinex_btc_usd,
            "Coinbase": coinbase_btc_usd,
            "Kraken": kraken_btc_usd,
            "Paribu": paribu_btc_usd,
            "OKX": okx_btc_usd,
            "Bitflyer": bitflyer_btc_usd
        }
        
        # Format the message
        message = format_price_message(btc_try_prices, btc_usd_prices)
        
        # Send the formatted message
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in price command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show top 5 currency pairs with highest volume.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "volume"):
        return
    
    try:
        top_pairs = await BTCTurkAPI.get_top_volume_pairs()
        
        if not top_pairs:
            await update.message.reply_text(
                "Üzgünüm, hacim bilgilerini alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        # Find BTC/TRY pair and its rank
        btc_try_pair = None
        btc_try_rank = None
        
        for i, pair in enumerate(top_pairs, 1):
            pair_name = pair.get('pair', '')
            
            # Check if this is BTC/TRY
            if pair_name == 'BTCTRY':
                btc_try_pair = pair
                btc_try_rank = i
        
        # If BTC/TRY is not in top 5, add it separately
        if not btc_try_pair:
            # Find BTC/TRY in all pairs
            all_pairs = await BTCTurkAPI.get_all_pairs()
            if all_pairs:
                for i, pair in enumerate(all_pairs, 1):
                    if pair.get('pair') == 'BTCTRY':
                        btc_try_pair = pair
                        btc_try_rank = i
                        break
        
        # Format the message
        message = format_volume_message(top_pairs, btc_try_pair, btc_try_rank)
        
        # Send the formatted message
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in volume command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def dollar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show USDT/TRY and USD/TRY exchange rates.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "dollar"):
        return
    
    try:
        # Send a loading message
        loading_msg = await update.message.reply_text("Döviz kurları alınıyor, lütfen bekleyin...")
        
        # Get USDT/TRY rate from BTCTurk
        usdt_try_rate = await BTCTurkAPI.get_usdt_try_rate()
        
        # Get USD/TRY rate from Yadio
        usd_try_rate = await ExchangesAPI.get_usd_try_rate()
        
        # Format the message
        message = format_dollar_message(usdt_try_rate, usd_try_rate)
        
        # Update the loading message with the results
        await loading_msg.edit_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in dollar command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def convert_100lira(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert 100 TRY to satoshi and send the result.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "100lira"):
        return
    
    try:
        # Send a loading message
        loading_msg = await update.message.reply_text("Hesaplanıyor, lütfen bekleyin...")
        
        # Fetch current exchange rate from BTCTurk
        btc_try_rate = await BTCTurkAPI.get_btc_try_price()
        
        if not btc_try_rate or btc_try_rate <= 0:
            await loading_msg.edit_text("Üzgünüm, geçersiz bir kur aldım. Lütfen daha sonra tekrar deneyin.")
            return
        
        # Format the message
        message = format_100lira_message(btc_try_rate)
        
        # Update the loading message with the results
        await loading_msg.edit_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Unexpected error in 100lira command: {str(e)}")
        await update.message.reply_text("Beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the ID of the current chat.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Only admin can use this command
    if update.effective_user.username != ADMIN_USERNAME:
        return
    
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Private Chat"
    
    message = f"Chat ID: `{chat_id}`\nChat Title: {chat_title}"
    
    await update.message.reply_text(message, parse_mode='Markdown')
