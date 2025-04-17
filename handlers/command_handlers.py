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
from api.lnbits import LNBitsAPI
from database.db import user_has_wallet, save_wallet, get_wallet
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
        "/dollar - USDT/TRY ve USD/TRY kurlarını göster\n"
        "/wallet - LNBits cüzdanı oluştur\n"
        "/invoice [miktar] - Belirtilen miktar için ödeme talebi oluştur\n"
        "/gimmecheese - 21 satoshi gönder"
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

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new LNBits wallet for the user or show existing wallet info.

    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return

    # Check rate limit
    if await check_rate_limit(update, "wallet"):
        return

    # Get the user ID
    user_id = str(update.effective_user.id)

    # Send a processing message
    processing_message = await update.message.reply_text("Cüzdan bilgileri kontrol ediliyor...")

    try:
        # Check if user already has a wallet
        if user_has_wallet(user_id):
            # Get existing wallet info from database
            wallet_data = get_wallet(user_id)

            if wallet_data:
                # Get the admin key for checking balance
                admin_key = wallet_data.get('admin_key')

                # Store wallet keys in user data for this session
                if not hasattr(context, 'user_data'):
                    context.user_data = {}

                context.user_data['wallet_id'] = wallet_data.get('wallet_id')
                context.user_data['wallet_adminkey'] = admin_key
                context.user_data['wallet_inkey'] = wallet_data.get('inkey')

                # Get real-time balance from LNBits API
                await processing_message.edit_text("Cüzdan bakiyesi kontrol ediliyor...")
                balance_result = await LNBitsAPI.get_wallet_balance(admin_key)

                if balance_result.get('status') == 'SUCCESS':
                    # Update balance in database
                    balance_sat = balance_result.get('balance_sat', 0)
                    from database.db import update_wallet_balance
                    update_wallet_balance(user_id, balance_sat)

                    # Format the wallet information with real-time balance
                    wallet_info = (
                        f"✅ Cüzdanınız zaten mevcut!\n"
                        f"💰 Bakiye: {balance_sat} SAT"
                    )
                else:
                    # Use stored balance if API call fails
                    wallet_info = (
                        f"✅ Cüzdanınız zaten mevcut!\n"
                        f"💰 Bakiye: {wallet_data.get('balance_sat', 0)} SAT"
                    )

                # Send wallet info to the chat
                await processing_message.edit_text(wallet_info, parse_mode='Markdown')
                return
            else:
                # This shouldn't happen, but just in case
                logger.error(f"Database inconsistency: user {user_id} has wallet but data not found")

        # User doesn't have a wallet, create a new one
        await processing_message.edit_text("LNBits cüzdanı oluşturuluyor...")

        # Create the wallet
        result = await LNBitsAPI.create_wallet(user_id)

        if result.get('status') == 'SUCCESS':
            wallet_data = result.get('wallet', {})

            # Save wallet to database
            save_success = save_wallet(
                telegram_id=user_id,
                wallet_id=wallet_data.get('id'),
                admin_key=wallet_data.get('adminkey'),
                inkey=wallet_data.get('inkey')
            )

            if not save_success:
                logger.error(f"Failed to save wallet to database for user {user_id}")

            # Format the wallet information without showing sensitive keys
            wallet_info = (
                f"✅ Cüzdan başarıyla oluşturuldu!\n"
                f"💰 Bakiye: 0 SAT"
            )

            # Store wallet keys in user data for this session
            if not hasattr(context, 'user_data'):
                context.user_data = {}

            context.user_data['wallet_id'] = wallet_data.get('id')
            context.user_data['wallet_adminkey'] = wallet_data.get('adminkey')
            context.user_data['wallet_inkey'] = wallet_data.get('inkey')

            # Send wallet info to the chat
            await processing_message.edit_text(wallet_info, parse_mode='Markdown')
        else:
            error_message = result.get('errors', [{}])[0].get('message', 'Bilinmeyen hata')
            await processing_message.edit_text(f"❌ Cüzdan oluşturulamadı: {error_message}")

    except Exception as e:
        logger.error(f"Error in wallet command: {str(e)}")
        await processing_message.edit_text(f"❌ Cüzdan işlemi sırasında bir hata oluştu: {str(e)}")

async def invoice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new invoice (Bolt11) for receiving funds.

    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if user is banned
    if await is_banned(update):
        return

    # Check rate limit
    if await check_rate_limit(update, "invoice"):
        return

    # Get the user ID
    user_id = str(update.effective_user.id)

    # Check if amount is provided
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ Kullanım: /invoice [miktar]\n"
            "Örnek: /invoice 21"
        )
        return

    # Parse the amount
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Miktar pozitif bir sayı olmalıdır.")
            return
    except ValueError:
        await update.message.reply_text("❌ Geçersiz miktar. Lütfen bir sayı girin.")
        return

    # Check if user has a wallet in the database
    if not user_has_wallet(user_id):
        await update.message.reply_text(
            "❌ Önce bir cüzdan oluşturmanız gerekiyor.\n"
            "/wallet komutunu kullanarak bir cüzdan oluşturun."
        )
        return

    # Get wallet data from database
    wallet_data = get_wallet(user_id)
    if not wallet_data or 'inkey' not in wallet_data:
        await update.message.reply_text(
            "❌ Cüzdan bilgilerinize erişilemiyor.\n"
            "Lütfen /wallet komutunu tekrar çalıştırın."
        )
        return

    # Get the wallet inkey
    wallet_inkey = wallet_data.get('inkey')

    # Send a message that we're creating the invoice
    processing_message = await update.message.reply_text(f"{amount} satoshi için fatura oluşturuluyor...")

    try:
        # Create the invoice
        memo = f"Yirmibir Bitcoin Bot - {amount} satoshi"
        result = await LNBitsAPI.create_invoice(wallet_inkey, amount, memo)

        if result.get('status') == 'SUCCESS':
            invoice_data = result.get('invoice', {})
            payment_request = invoice_data.get('payment_request', '')

            if not payment_request:
                await processing_message.edit_text("❌ Fatura oluşturulurken bir hata oluştu.")
                return

            # Get the payment hash for later checking
            payment_hash = invoice_data.get('payment_hash', '')

            # Format the invoice information
            invoice_info = (
                f"✅ {amount} satoshi için fatura oluşturuldu!\n\n"
                f"`{payment_request}`\n\n"
                f"Bu fatura ödendikten sonra, bakiyeniz otomatik olarak güncellenecektir."
            )

            # Send invoice info to the chat
            await processing_message.edit_text(invoice_info, parse_mode='Markdown')

            # Schedule a task to check payment status after a delay
            if payment_hash:
                # Wait 30 seconds before checking payment status
                await asyncio.sleep(30)

                # Get wallet data again to ensure we have the latest keys
                wallet_data = get_wallet(user_id)
                if not wallet_data:
                    logger.error(f"Failed to get wallet data for payment check: {user_id}")
                    return

                # Check if payment was received
                admin_key = wallet_data.get('admin_key')
                payment_result = await LNBitsAPI.check_payment_status(admin_key, payment_hash)

                if payment_result.get('status') == 'SUCCESS' and payment_result.get('paid', False):
                    # Payment received, update balance
                    balance_result = await LNBitsAPI.get_wallet_balance(admin_key)

                    if balance_result.get('status') == 'SUCCESS':
                        # Update balance in database
                        balance_sat = balance_result.get('balance_sat', 0)
                        from database.db import update_wallet_balance
                        update_wallet_balance(user_id, balance_sat)

                        # Send notification to user
                        await update.message.reply_text(
                            f"💰 Ödeme alındı! Yeni bakiyeniz: {balance_sat} SAT"
                        )
        else:
            error_message = result.get('errors', [{}])[0].get('message', 'Bilinmeyen hata')
            await processing_message.edit_text(f"❌ Fatura oluşturulamadı: {error_message}")

    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        await processing_message.edit_text(f"❌ Fatura oluşturulurken bir hata oluştu: {str(e)}")
