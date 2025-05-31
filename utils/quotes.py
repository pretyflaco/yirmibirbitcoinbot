"""Quotes utility for the Telegram bot.

This module provides functions to load and manage Satoshi Nakamoto quotes
for the bot to share with users.
"""

import json
import random
import logging
import time
from typing import Dict, Any, Optional, List, Set

from telegram.ext import ContextTypes
from config import QUOTE_INTERVAL, QUOTE_SOURCE_URL

# Set up logging
logger = logging.getLogger(__name__)

# Store for quotes
quotes = []
replied_to_messages: Set[int] = set()

def load_quotes() -> List[Dict[str, Any]]:
    """Load quotes from JSON files.
    
    First tries to load Turkish quotes, then falls back to English quotes if needed.
    
    Returns:
        List of quote dictionaries
    """
    global quotes
    
    if quotes:
        return quotes
        
    try:
        # Use Turkish quotes file
        with open('quotes_tr.json', 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        logger.info(f"Loaded {len(quotes)} Turkish Satoshi quotes")
    except Exception as e:
        logger.error(f"Error loading Turkish quotes: {str(e)}")
        # Fallback to English quotes if Turkish file is not available
        try:
            with open('quotes.json', 'r', encoding='utf-8') as f:
                quotes = json.load(f)
            logger.info(f"Loaded {len(quotes)} English Satoshi quotes (fallback)")
        except Exception as e:
            logger.error(f"Error loading English quotes: {str(e)}")
            quotes = []
    
    return quotes

def get_random_quote() -> Optional[Dict[str, Any]]:
    """Get a random quote.
    
    Returns:
        A random quote dictionary, or None if no quotes are available
    """
    all_quotes = load_quotes()
    if all_quotes:
        return random.choice(all_quotes)
    return None

async def post_quote(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Post a random quote to all tracked chats.
    
    Args:
        context: The context object for the bot
    """
    try:
        # Get all tracked chats where the bot is a member
        tracked_chats = context.bot_data.get('quote_chats', set())
        logger.info(f"Attempting to post quote to {len(tracked_chats)} tracked chats")
        
        if not tracked_chats:
            logger.warning("No tracked chats found for quote posting")
            return
            
        # Get a random quote
        quotes = context.bot_data.get('quotes', [])
        if not quotes:
            logger.error("No quotes available to post")
            return
            
        quote = random.choice(quotes)
        
        # Format the quote message in Turkish
        message = f"💭 *Satoshi Nakamoto'dan bir alıntı:*\n\n_{quote['text']}_"
        
        # Post to each tracked chat
        for chat_id in tracked_chats:
            try:
                # Check if enough time has passed since last post
                last_time = context.bot_data.get('last_quote_time', {}).get(str(chat_id), 0)
                current_time = time.time()
                
                # Allow posting if it's the first time (last_time is 0) or enough time has passed
                if last_time == 0 or current_time - last_time >= QUOTE_INTERVAL:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    # Update last quote time for this specific chat
                    if 'last_quote_time' not in context.bot_data:
                        context.bot_data['last_quote_time'] = {}
                    context.bot_data['last_quote_time'][str(chat_id)] = current_time
                    logger.info(f"Successfully posted Turkish quote to chat {chat_id}")
                else:
                    logger.info(f"Skipping quote post to chat {chat_id} - too soon since last post")
            except Exception as e:
                logger.error(f"Failed to post quote to chat {chat_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in post_quote: {e}")

async def quote_scheduler(application) -> None:
    """Schedule quote posting using asyncio.
    
    Args:
        application: The bot application object
    """
    while True:
        try:
            # Post quotes to all tracked chats
            for chat_id in application.bot_data.get('quote_chats', set()):
                current_time = time.time()
                last_time = application.bot_data.get('last_quote_time', {}).get(str(chat_id), 0)
                
                if current_time - last_time >= QUOTE_INTERVAL:
                    quotes = application.bot_data.get('quotes', [])
                    if quotes:
                        quote = random.choice(quotes)
                        message = f"💭 *Satoshi Nakamoto'dan bir alıntı:*\n\n_{quote['text']}_"
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                        # Update last quote time for this specific chat
                        if 'last_quote_time' not in application.bot_data:
                            application.bot_data['last_quote_time'] = {}
                        application.bot_data['last_quote_time'][str(chat_id)] = current_time
                        logger.info(f"Posted Turkish quote to chat {chat_id}")
                    else:
                        logger.error("No quotes available to post")
        except Exception as e:
            logger.error(f"Error in quote scheduler: {str(e)}")
        
        # Wait for the next interval
        await asyncio.sleep(QUOTE_INTERVAL)
