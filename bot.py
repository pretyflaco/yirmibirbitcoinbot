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
    ConversationHandler,
    PersistenceInput,
    PicklePersistence,
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
from config import TELEGRAM_BOT_TOKEN, ADMIN_USERNAME, QUOTE_INTERVAL, RSS_CHECK_INTERVAL, YOUTUBE_CHECK_INTERVAL, BLOG_CHECK_INTERVAL, BOT_STATE_FILE

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
from utils.rss_monitor import check_for_new_episode
from utils.blog_monitor import check_for_new_blog_post, post_latest_blog_command
from utils.youtube_monitor import check_for_new_video

YIRMIBIR_GROUP_ID = -1001431368885  # @YirmibirBitcoin


async def post_init(application: Application) -> None:
    """Seed bot_data after persistence has loaded it.

    PicklePersistence replaces application.bot_data during initialize(), so
    anything put into bot_data in main() before run_polling would be lost.
    Static/derived values are (re)set here on every start.
    """
    bot_data = application.bot_data

    # Quotes are reloaded from the JSON files on every start.
    try:
        with open('quotes_tr.json', 'r', encoding='utf-8') as f:
            bot_data['quotes'] = json.load(f)
        logger.info(f"Loaded {len(bot_data['quotes'])} Turkish Satoshi quotes")
    except Exception as e:
        logger.error(f"Error loading Turkish quotes: {str(e)}")
        try:
            with open('quotes.json', 'r', encoding='utf-8') as f:
                bot_data['quotes'] = json.load(f)
            logger.info(f"Loaded {len(bot_data['quotes'])} English Satoshi quotes (fallback)")
        except Exception as e:
            logger.error(f"Error loading English quotes: {str(e)}")
            bot_data['quotes'] = []

    bot_data.setdefault('quote_chats', set()).add(YIRMIBIR_GROUP_ID)
    logger.info(f"Manually added YirmibirBitcoin group ({YIRMIBIR_GROUP_ID}) to tracked chats")

    # With persisted posted-sets, monitors only need to prime when the set is
    # empty (very first run). Reset the per-process primed flags so that logic
    # is decided by the monitors, not by stale flags from the state file.
    for flag, key in (('episode_monitor_primed', 'posted_episode_links'),
                      ('video_monitor_primed', 'posted_video_links'),
                      ('blog_monitor_primed', 'posted_blog_ids')):
        bot_data[flag] = bool(bot_data.get(key))
    # Legacy seed (pre-dates the startup priming); harmless to keep.
    posted_videos = bot_data.setdefault('posted_video_links', set())
    posted_videos.add('https://youtu.be/eNw-xsqOlfE')
    posted_videos.add('https://www.youtube.com/watch?v=eNw-xsqOlfE')


    logger.info(
        "Restored state: %d episodes, %d videos, %d blog posts already posted",
        len(bot_data.get('posted_episode_links', ())),
        len(bot_data.get('posted_video_links', ())),
        len(bot_data.get('posted_blog_ids', ())),
    )


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    # Persist bot_data only (posted-item sets, tracked chats). user_data is NOT
    # persisted on purpose: it holds LNbits wallet admin keys.
    persistence = PicklePersistence(
        filepath=BOT_STATE_FILE,
        store_data=PersistenceInput(bot_data=True, chat_data=False, user_data=False, callback_data=False),
        update_interval=60,
    )
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

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
    application.add_handler(CommandHandler("sonyazi", post_latest_blog_command))

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

    # Automatic Satoshi quote posting has been removed (see utils/quotes.py).
    logger.info("Automatic quote posting: removed")

    # Set up RSS feed monitoring
    try:
        application.job_queue.run_repeating(check_for_new_episode, interval=RSS_CHECK_INTERVAL, first=30)
        logger.info("RSS feed monitoring started")
    except Exception as e:
        logger.error(f"Error setting up RSS monitoring: {str(e)}")

    # Set up YouTube monitoring
    try:
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
