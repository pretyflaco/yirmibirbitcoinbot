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
LIGHTNING_ADDRESS = 1

# Flag to track if a lightning payment is in progress
lightning_payment_in_progress = False

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
    
    # Ask for Lightning Address
    await update.message.reply_text(
        "Lütfen Bitcoin göndermek istediğiniz Lightning Adresini girin.\n"
        "Örnek: satoshi@lightning.com\n\n"
        "İptal etmek için /cancel yazın."
    )
    
    return LIGHTNING_ADDRESS

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
        
        # Check if we have enough balance (at least 1000 sats)
        if int(btc_wallet.get('balance', 0)) < 1000:
            await processing_message.edit_text("Yetersiz bakiye. En az 1000 satoshi gerekiyor.")
            lightning_payment_in_progress = False
            return ConversationHandler.END
        
        # Send the payment
        payment_result = await BlinkAPI.send_lightning_payment(lightning_address, 1000)
        
        if payment_result.get('status') == 'SUCCESS':
            await processing_message.edit_text(
                f"✅ Ödeme başarıyla gönderildi!\n\n"
                f"Alıcı: {lightning_address}\n"
                f"Miktar: 1000 satoshi"
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
