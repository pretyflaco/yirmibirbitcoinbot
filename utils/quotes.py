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
from config import QUOTE_SOURCE_URL

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

# Scheduled quote posting (post_quote / quote_scheduler) was removed on purpose:
# the daily, poorly translated Satoshi quotes were driving activity out of the
# @YirmibirBitcoin group. Do not reintroduce automatic quote posting.
