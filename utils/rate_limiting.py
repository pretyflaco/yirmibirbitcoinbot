"""Rate limiting utility for the Telegram bot.

This module provides functions to implement rate limiting for bot commands
to prevent abuse and ensure fair usage.
"""

import time
import logging
from typing import Dict, Any, Optional, Set
from telegram import Update

from config import ADMIN_USERNAME, PRIVATE_CHAT_COOLDOWN, PUBLIC_GROUP_COOLDOWN

# Set up logging
logger = logging.getLogger(__name__)

# Store for rate limiting
command_last_used: Dict[str, float] = {}
banned_users: Set[str] = set()

async def is_banned(update: Update) -> bool:
    """Check if the user is banned.
    
    Args:
        update: The Telegram update object
        
    Returns:
        True if the user is banned, False otherwise
    """
    if update.effective_user.username:
        return update.effective_user.username in banned_users
    return False

async def check_rate_limit(update: Update, command: str) -> bool:
    """Check if the command is rate limited.
    
    Args:
        update: The Telegram update object
        command: The command being executed
        
    Returns:
        True if the command is rate limited, False otherwise
    """
    # Admin is exempt from rate limits
    if update.effective_user.username == ADMIN_USERNAME:
        return False
    
    # Get the chat ID and type
    chat_id = update.effective_chat.id
    is_private = update.effective_chat.type == "private"
    
    # Create a unique key for this command in this chat
    key = f"{command}_{chat_id}"
    
    # Get the current time
    current_time = time.time()
    
    # Check if the command has been used before
    if key in command_last_used:
        # Calculate the time elapsed since last use
        elapsed = current_time - command_last_used[key]
        
        # Check if the cooldown period has passed
        cooldown = PRIVATE_CHAT_COOLDOWN if is_private else PUBLIC_GROUP_COOLDOWN
        if elapsed < cooldown:
            # Calculate remaining time
            remaining = int(cooldown - elapsed)
            minutes = remaining // 60
            seconds = remaining % 60
            
            # Send a message about the rate limit
            await update.message.reply_text(
                f"Bu komutu tekrar kullanmak için {minutes} dakika {seconds} saniye beklemelisiniz."
            )
            return True
    
    # Update the last used time
    command_last_used[key] = current_time
    return False

def ban_user(username: str) -> bool:
    """Ban a user from using the bot.
    
    Args:
        username: The username to ban
        
    Returns:
        True if the user was banned, False if the user was already banned
    """
    if username in banned_users:
        return False
    
    banned_users.add(username)
    return True
