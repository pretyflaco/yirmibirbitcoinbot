"""Conversation handlers for the Telegram bot.

This module contains handler functions for multi-step conversations with the bot.
"""

import logging
from typing import Dict, Any, Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from api.blink import BlinkAPI
from utils.rate_limiting import is_banned, check_rate_limit
from config import ADMIN_USERNAME

# Set up logging
logger = logging.getLogger(__name__)

# Define conversation states for the gimmecheese command
PAYMENT_TYPE = 1
LIGHTNING_ADDRESS = 2
LIGHTNING_INVOICE = 3

# Flag to track if a lightning payment is in progress
lightning_payment_in_progress = False

# Amount to send in satoshis
CHEESE_AMOUNT_SATS = 21

async def gimmecheese_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of sending Bitcoin via Lightning Network.

    Args:
        update: The update object from Telegram
        context: The context object for the bot

    Returns:
        The next conversation state
    """
    # Check if user is banned
    if await is_banned(update):
        return ConversationHandler.END

    # Check rate limit
    if await check_rate_limit(update, "gimmecheese"):
        return ConversationHandler.END

    # Only allow admin to use this command
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Bu komutu sadece bot yöneticisi kullanabilir.")
        return ConversationHandler.END

    # Check if this is a private chat
    if update.effective_chat.type != "private":
        await update.message.reply_text("Bu komut sadece özel mesajlarda kullanılabilir.")
        return ConversationHandler.END

    # Check if a payment is already in progress
    global lightning_payment_in_progress
    if lightning_payment_in_progress:
        await update.message.reply_text("Zaten bir ödeme işlemi devam ediyor. Lütfen bekleyin.")
        return ConversationHandler.END

    # Check if BLINK_API_KEY is set
    from config import BLINK_API_KEY
    if not BLINK_API_KEY:
        await update.message.reply_text(
            "Blink API anahtarı ayarlanmamış. Lütfen .env dosyasında BLINK_API_KEY değerini güncelleyin."
        )
        return ConversationHandler.END

    # Ask for payment type
    await update.message.reply_text(
        "Bitcoin göndermek için bir yöntem seçin:\n\n"
        "1️⃣ Lightning Adresi (örn: satoshi@lightning.com)\n"
        "2️⃣ Lightning Faturası (BOLT11 invoice)\n\n"
        "Lütfen 1 veya 2 yazarak seçiminizi yapın.\n"
        "İptal etmek için /cancel yazın."
    )

    return PAYMENT_TYPE

async def process_payment_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the payment type selection.

    Args:
        update: The update object from Telegram
        context: The context object for the bot

    Returns:
        The next conversation state
    """
    # Check if this is a cancel command
    if update.message.text.lower() == "/cancel":
        await update.message.reply_text("İşlem iptal edildi.")
        return ConversationHandler.END

    # Get the payment type
    payment_type = update.message.text.strip()

    # Process based on selection
    if payment_type == "1":
        # User chose Lightning Address
        await update.message.reply_text(
            "Lütfen Bitcoin göndermek istediğiniz Lightning Adresini girin.\n"
            "Örnek: satoshi@lightning.com\n\n"
            "İptal etmek için /cancel yazın."
        )
        return LIGHTNING_ADDRESS
    elif payment_type == "2":
        # User chose Lightning Invoice
        await update.message.reply_text(
            "Lütfen ödemek istediğiniz Lightning Faturasını (BOLT11 invoice) girin.\n"
            "Örnek: lnbc...\n\n"
            "İptal etmek için /cancel yazın."
        )
        return LIGHTNING_INVOICE
    else:
        # Invalid selection
        await update.message.reply_text(
            "Geçersiz seçim. Lütfen 1 (Lightning Adresi) veya 2 (Lightning Faturası) yazın.\n"
            "İptal etmek için /cancel yazın."
        )
        return PAYMENT_TYPE

async def process_lightning_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the Lightning Address and send Bitcoin.

    Args:
        update: The update object from Telegram
        context: The context object for the bot

    Returns:
        The next conversation state
    """
    global lightning_payment_in_progress

    # Check if this is a cancel command
    if update.message.text.lower() == "/cancel":
        await update.message.reply_text("İşlem iptal edildi.")
        return ConversationHandler.END

    # Get the Lightning Address
    lightning_address = update.message.text.strip()

    # Validate the Lightning Address format
    if not "@" in lightning_address:
        await update.message.reply_text(
            "Geçersiz Lightning Adresi formatı. Lütfen 'kullanıcı@domain.com' formatında bir adres girin."
        )
        return LIGHTNING_ADDRESS

    # Set payment in progress flag
    lightning_payment_in_progress = True

    # Send a message that we're processing
    processing_message = await update.message.reply_text("Lightning ödemesi işleniyor...")

    try:
        # Get the wallet ID and check balance
        wallet_data = await BlinkAPI.get_wallet_data()
        if not wallet_data:
            await processing_message.edit_text("Cüzdan bilgileri alınamadı. Lütfen daha sonra tekrar deneyin.")
            lightning_payment_in_progress = False
            return ConversationHandler.END

        # Find the BTC wallet
        btc_wallet = None
        for wallet in wallet_data:
            if wallet.get('walletCurrency') == 'BTC':
                btc_wallet = wallet
                break

        if not btc_wallet:
            await processing_message.edit_text("BTC cüzdanı bulunamadı.")
            lightning_payment_in_progress = False
            return ConversationHandler.END

        # Check if we have enough balance (at least CHEESE_AMOUNT_SATS)
        if int(btc_wallet.get('balance', 0)) < CHEESE_AMOUNT_SATS:
            await processing_message.edit_text(f"Yetersiz bakiye. En az {CHEESE_AMOUNT_SATS} satoshi gerekiyor.")
            lightning_payment_in_progress = False
            return ConversationHandler.END

        # Send the payment
        payment_result = await BlinkAPI.send_lightning_payment(lightning_address, CHEESE_AMOUNT_SATS)

        if payment_result.get('status') == 'SUCCESS':
            await processing_message.edit_text(
                f"✅ Ödeme başarıyla gönderildi!\n\n"
                f"Alıcı: {lightning_address}\n"
                f"Miktar: {CHEESE_AMOUNT_SATS} satoshi"
            )
        else:
            error_message = payment_result.get('errors', [{}])[0].get('message', 'Bilinmeyen hata')
            await processing_message.edit_text(f"❌ Ödeme gönderilemedi: {error_message}")

    except Exception as e:
        logger.error(f"Error in lightning payment: {str(e)}")
        await processing_message.edit_text(f"Bir hata oluştu: {str(e)}")

    finally:
        # Reset payment in progress flag
        lightning_payment_in_progress = False

    return ConversationHandler.END

async def process_lightning_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the Lightning Invoice and pay it.

    Args:
        update: The update object from Telegram
        context: The context object for the bot

    Returns:
        The next conversation state
    """
    global lightning_payment_in_progress

    # Check if this is a cancel command
    if update.message.text.lower() == "/cancel":
        await update.message.reply_text("İşlem iptal edildi.")
        return ConversationHandler.END

    # Get the Lightning Invoice
    payment_request = update.message.text.strip()

    # Basic validation of the invoice format
    if not payment_request.startswith("ln"):
        await update.message.reply_text(
            "Geçersiz Lightning Faturası formatı. Fatura 'ln' ile başlamalıdır.\n"
            "Lütfen geçerli bir BOLT11 faturası girin."
        )
        return LIGHTNING_INVOICE

    # Set payment in progress flag
    lightning_payment_in_progress = True

    # Send a message that we're processing
    processing_message = await update.message.reply_text("Lightning ödemesi işleniyor...")

    try:
        # Pay the invoice
        payment_result = await BlinkAPI.pay_lightning_invoice(payment_request)

        if payment_result.get('status') == 'SUCCESS':
            await processing_message.edit_text(
                f"✅ Ödeme başarıyla gönderildi!\n\n"
                f"Fatura: {payment_request[:20]}...{payment_request[-10:]}\n"
            )
        else:
            error_message = payment_result.get('errors', [{}])[0].get('message', 'Bilinmeyen hata')
            await processing_message.edit_text(f"\u274c Ödeme gönderilemedi: {error_message}")

    except Exception as e:
        logger.error(f"Error in lightning invoice payment: {str(e)}")
        await processing_message.edit_text(f"Bir hata oluştu: {str(e)}")

    finally:
        # Reset payment in progress flag
        lightning_payment_in_progress = False

    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation.

    Args:
        update: The update object from Telegram
        context: The context object for the bot

    Returns:
        The next conversation state
    """
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END
