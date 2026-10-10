#!/usr/bin/env python
"""Telegram Bitcoin Converter Bot main module.

This module initializes and runs the Telegram bot that provides
Bitcoin price information, currency conversion, and other related functionalities.
"""

import os
import logging
import asyncio
import json
import time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)

# Import API clients
from api.lnbits import LNBitsAPI

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# httpx logs every request URL at INFO, and Telegram Bot API URLs embed the bot
# token (https://api.telegram.org/bot<TOKEN>/...). Keep it at WARNING so the
# token never reaches the journal.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Import configuration
from config import TELEGRAM_BOT_TOKEN, ADMIN_USERNAME, QUOTE_INTERVAL, RSS_CHECK_INTERVAL, YOUTUBE_CHECK_INTERVAL, BLOG_CHECK_INTERVAL

# Import handlers
from handlers.command_handlers import (
    start,
    help_command,
    ban_command,
    price_command,
    volume_command,
    dollar_command,
    convert_100lira,
    get_group_id,
    wallet_command,
    invoice_command
)
from handlers.conversation_handlers import (
    gimmecheese_command,
    process_payment_input,
    cancel_command,
    PAYMENT_INPUT
)
from handlers.message_handlers import (
    handle_source_request,
    track_new_chat
)

# Import utilities
from utils.quotes import post_quote, quote_scheduler, load_quotes
from utils.rss_monitor import check_for_new_episode
from utils.blog_monitor import check_for_new_blog_post
from utils.youtube_monitor import check_for_new_video

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Load quotes and store them in application.bot_data
    try:
        # Try to load Turkish quotes first
        with open('quotes_tr.json', 'r', encoding='utf-8') as f:
            application.bot_data['quotes'] = json.load(f)
        logger.info(f"Loaded {len(application.bot_data['quotes'])} Turkish Satoshi quotes")
    except Exception as e:
        logger.error(f"Error loading Turkish quotes: {str(e)}")
        # Fallback to English quotes if Turkish file is not available
        try:
            with open('quotes.json', 'r', encoding='utf-8') as f:
                application.bot_data['quotes'] = json.load(f)
            logger.info(f"Loaded {len(application.bot_data['quotes'])} English Satoshi quotes (fallback)")
        except Exception as e:
            logger.error(f"Error loading English quotes: {str(e)}")
            application.bot_data['quotes'] = []

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("100lira", convert_100lira))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("volume", volume_command))
    application.add_handler(CommandHandler("dollar", dollar_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("groupid", get_group_id))
    application.add_handler(CommandHandler("wallet", wallet_command))
    application.add_handler(CommandHandler("invoice", invoice_command))

    # Add conversation handler for gimmecheese command
    gimmecheese_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("gimmecheese", gimmecheese_command)],
        states={
            PAYMENT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_payment_input)]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)]
    )
    application.add_handler(gimmecheese_conv_handler)

    # Add handlers for tracking new chats and handling source requests
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_chat))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, handle_source_request))

    # Initialize quote_chats if it doesn't exist
    if 'quote_chats' not in application.bot_data:
        application.bot_data['quote_chats'] = set()

    # Manually add the YirmibirBitcoin group to tracked chats
    yirmibir_group_id = -1001431368885  # The actual group ID for @YirmibirBitcoin
    application.bot_data['quote_chats'].add(yirmibir_group_id)
    logger.info(f"Manually added YirmibirBitcoin group ({yirmibir_group_id}) to tracked chats")

    # Daily Satoshi quote posting intentionally disabled.
    # (Previously registered post_quote via job_queue.run_repeating / quote_scheduler.)
    # try:
    #     if application.job_queue:
    #         application.job_queue.run_repeating(post_quote, interval=QUOTE_INTERVAL, first=10)
    #         logger.info("Using job queue for quote scheduling")
    #     else:
    #         # Create a task for quote scheduling
    #         asyncio.create_task(quote_scheduler(application))
    #         logger.info("Using asyncio task for quote scheduling")
    # except Exception as e:
    #     logger.error(f"Error setting up quote scheduling: {str(e)}")
    #     # Fallback to asyncio task
    #     asyncio.create_task(quote_scheduler(application))
    #     logger.info("Using asyncio task for quote scheduling (fallback)")
    logger.info("Daily Satoshi quote scheduling is disabled")

    # Set up RSS feed monitoring
    try:
        application.job_queue.run_repeating(check_for_new_episode, interval=RSS_CHECK_INTERVAL, first=30)
        logger.info("RSS feed monitoring started")
    except Exception as e:
        logger.error(f"Error setting up RSS monitoring: {str(e)}")

    # Set up YouTube monitoring
    try:
        # Initialize with the starting video to avoid reposting it
        if 'posted_video_links' not in application.bot_data:
            application.bot_data['posted_video_links'] = set()
        # Add the video that was published today so we don't repost it
        application.bot_data['posted_video_links'].add('https://youtu.be/eNw-xsqOlfE')
        application.bot_data['posted_video_links'].add('https://www.youtube.com/watch?v=eNw-xsqOlfE')
        logger.info("Initialized YouTube monitor with existing video")
        
        application.job_queue.run_repeating(check_for_new_video, interval=YOUTUBE_CHECK_INTERVAL, first=60)
        logger.info("YouTube monitoring started")
    except Exception as e:
        logger.error(f"Error setting up YouTube monitoring: {str(e)}")

    # Set up yirmibir.org blog monitoring (first check primes existing posts)
    try:
        application.job_queue.run_repeating(check_for_new_blog_post, interval=BLOG_CHECK_INTERVAL, first=90)
        logger.info("Blog monitoring started")
    except Exception as e:
        logger.error(f"Error setting up blog monitoring: {str(e)}")

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
