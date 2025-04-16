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
PAYMENT_INPUT = 1

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

    # Ask for payment input
    await update.message.reply_text(
        "Bitcoin göndermek için lütfen bir Lightning Adresi veya Lightning Faturası (BOLT11 invoice) girin.\n\n"
        "Lightning Adresi örneği: satoshi@lightning.com\n"
        "Lightning Faturası örneği: lnbc...\n\n"
        "Sadece 21 satoshi gönderebilirim.\n"
        "İptal etmek için /cancel yazın."
    )

    return PAYMENT_INPUT

async def process_payment_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the payment input and handle different payment types.

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

    # Get the payment input
    payment_input = update.message.text.strip()

    # Detect the payment type
    payment_info = BlinkAPI.detect_payment_type(payment_input)
    payment_type = payment_info.get('type')

    # Set payment in progress flag
    lightning_payment_in_progress = True

    # Send a message that we're processing
    processing_message = await update.message.reply_text("Lightning ödemesi işleniyor...")

    try:
        # Handle different payment types
        if payment_type == "lightning_address":
            # Process Lightning Address
            lightning_address = payment_info.get('value')

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

            # Check if we have enough balance
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
                await processing_message.edit_text(f"\u274c Ödeme gönderilemedi: {error_message}")

        elif payment_type == "bolt11_with_amount":
            # Process Bolt11 invoice with amount
            invoice = payment_info.get('value')
            invoice_amount = payment_info.get('amount', 0)

            # Check if the invoice amount is greater than our limit
            if invoice_amount > CHEESE_AMOUNT_SATS:
                await processing_message.edit_text(
                    f"\u274c Fatura tutarı ({invoice_amount} satoshi) izin verilen maksimum tutarı ({CHEESE_AMOUNT_SATS} satoshi) aşıyor.\n"
                    f"Lütfen {CHEESE_AMOUNT_SATS} satoshi veya daha az bir fatura oluşturun."
                )
                lightning_payment_in_progress = False
                return ConversationHandler.END

            # Pay the invoice
            payment_result = await BlinkAPI.pay_lightning_invoice(invoice)

            if payment_result.get('status') == 'SUCCESS':
                await processing_message.edit_text(
                    f"✅ Ödeme başarıyla gönderildi!\n\n"
                    f"Fatura: {invoice[:20]}...{invoice[-10:]}\n"
                    f"Miktar: {invoice_amount} satoshi"
                )
            else:
                error_message = payment_result.get('errors', [{}])[0].get('message', 'Bilinmeyen hata')
                await processing_message.edit_text(f"\u274c Ödeme gönderilemedi: {error_message}")

        elif payment_type == "bolt11_no_amount":
            # Process Bolt11 invoice with no amount
            invoice = payment_info.get('value')

            # Pay the invoice with our fixed amount
            payment_result = await BlinkAPI.pay_no_amount_lightning_invoice(invoice, CHEESE_AMOUNT_SATS)

            if payment_result.get('status') == 'SUCCESS':
                await processing_message.edit_text(
                    f"✅ Ödeme başarıyla gönderildi!\n\n"
                    f"Fatura: {invoice[:20]}...{invoice[-10:]}\n"
                    f"Miktar: {CHEESE_AMOUNT_SATS} satoshi"
                )
            else:
                error_message = payment_result.get('errors', [{}])[0].get('message', 'Bilinmeyen hata')
                await processing_message.edit_text(f"\u274c Ödeme gönderilemedi: {error_message}")

        elif payment_type == "bolt11_unknown":
            # Unknown Bolt11 invoice format
            await processing_message.edit_text(
                "\u274c Fatura formatı tanınamadı. Lütfen geçerli bir Lightning Adresi veya BOLT11 faturası girin."
            )

        else:
            # Unknown payment type
            await processing_message.edit_text(
                "\u274c Geçersiz ödeme formatı. Lütfen geçerli bir Lightning Adresi (kullanıcı@domain.com) veya BOLT11 faturası (lnbc...) girin."
            )

    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
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
