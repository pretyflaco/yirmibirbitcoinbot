"""Message handlers for the Telegram bot.

This module contains handler functions for processing non-command messages.
"""

import logging
from typing import Dict, Any, Optional, Set

from telegram import Update
from telegram.ext import ContextTypes

from utils.quotes import get_random_quote, replied_to_messages
from config import QUOTE_SOURCE_URL

# Set up logging
logger = logging.getLogger(__name__)

async def handle_source_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle requests for quote source.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    # Check if this is a reply to a bot message
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user.is_bot:
        return
    
    # Check if the message contains "source" or "kaynak"
    message_text = update.message.text.lower()
    if "source" not in message_text and "kaynak" not in message_text:
        return
    
    # Check if we've already replied to this message
    message_id = update.message.message_id
    if message_id in replied_to_messages:
        return
    
    # Get the quote from the bot's message
    bot_message = update.message.reply_to_message.text
    
    # Find the quote in our database
    quotes = context.bot_data.get('quotes', [])
    for quote in quotes:
        if quote['text'] in bot_message:
            # Format the source information
            source_info = f"*Source:* {quote['date']}\n"
            if 'medium' in quote:
                source_info += f"*Medium:* {quote['medium']}\n"
            if 'post_id' in quote:
                source_info += f"*Post ID:* {quote['post_id']}\n"
            source_info += f"*More quotes:* {QUOTE_SOURCE_URL}"
            
            # Reply with the source information
            await update.message.reply_text(
                text=source_info,
                parse_mode='Markdown'
            )
            
            # Mark this message as replied to
            replied_to_messages.add(message_id)
            break

async def track_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Track new chats where the bot is added.
    
    Args:
        update: The update object from Telegram
        context: The context object for the bot
    """
    if update.my_chat_member and update.my_chat_member.new_chat_member.status == "member":
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title or "Private Chat"
        
        # Initialize quote_chats if it doesn't exist
        if 'quote_chats' not in context.bot_data:
            context.bot_data['quote_chats'] = set()
            logger.info("Initialized quote_chats set in bot_data")
        
        # Add the chat to tracked chats
        context.bot_data['quote_chats'].add(chat_id)
        logger.info(f"Bot added to chat {chat_id} ({chat_title}), now tracking for quote posts")
        
        # Log the current number of tracked chats
        tracked_chats_count = len(context.bot_data['quote_chats'])
        logger.info(f"Currently tracking {tracked_chats_count} chats for quote posts")
        
        # Post a welcome message with a quote
        try:
            quote = get_random_quote()
            if quote:
                message = (
                    f"👋 Merhaba! Ben Bitcoin fiyatları ve Satoshi Nakamoto alıntıları paylaşan bir botum.\n\n"
                    f"💬 *İlk Satoshi Alıntısı:*\n\n{quote['text']}"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Posted welcome message with quote to chat {chat_id}")
        except Exception as e:
            logger.error(f"Error posting welcome message to chat {chat_id}: {str(e)}")
