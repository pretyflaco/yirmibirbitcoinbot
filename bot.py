#!/usr/bin/env python
# Python Telegram Bot Implementation with v22.0

import os
import logging
import asyncio
import requests
import json
import time
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import API configuration
from config import (
    TELEGRAM_BOT_TOKEN, 
    BTCTURK_API_TICKER_URL,
    BLINK_API_URL,
    BLINK_PRICE_QUERY,
    BLINK_PRICE_VARIABLES,
    BLINK_API_KEY
)

# Yadio API URL
YADIO_API_URL = "https://api.yadio.io/exrates/USD"

# Additional API URLs
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"
KRAKEN_API_URL = "https://api.kraken.com/0/public/Ticker"
PARIBU_API_URL = "https://www.paribu.com/ticker"
BITFINEX_API_URL = "https://api-pub.bitfinex.com/v2/ticker"
BITSTAMP_API_URL = "https://www.bitstamp.net/api/v2/ticker"
COINBASE_API_URL = "https://api.coinbase.com/v2/prices"
OKX_API_URL = "https://www.okx.com/api/v5/market/ticker"
BITFLYER_API_URL = "https://api.bitflyer.com/v1/ticker"

# Rate limiting settings
PUBLIC_GROUP_COOLDOWN = 3600  # 1 hour in seconds
PRIVATE_CHAT_COOLDOWN = 900   # 15 minutes in seconds
ADMIN_USERNAME = "pretyflaco"

# Quote posting settings
QUOTE_INTERVAL = 12 * 60 * 60  # 12 hours in seconds
QUOTE_SOURCE_URL = "https://github.com/dergigi/QuotableSatoshi"

# Define conversation states for the gimmecheese command
LIGHTNING_ADDRESS = 1

# Store for rate limiting
command_last_used = {}
banned_users = set()
quotes = []
last_quote_time = {}
replied_to_messages = set()
quote_task = None
lightning_payment_in_progress = False

# Load quotes from JSON file
def load_quotes():
    global quotes
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

# Get a random quote
def get_random_quote():
    if not quotes:
        load_quotes()
    if quotes:
        return random.choice(quotes)
    return None

async def is_banned(update: Update) -> bool:
    """Check if the user is banned."""
    if update.effective_user.username:
        return update.effective_user.username in banned_users
    return False

async def check_rate_limit(update: Update, command: str) -> bool:
    """Check if the command is rate limited."""
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

async def post_quote(context: ContextTypes.DEFAULT_TYPE):
    """Post a random quote to all tracked chats."""
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

async def quote_scheduler(application):
    """Schedule quote posting using asyncio."""
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

async def handle_source_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle requests for quote source."""
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
    """Track new chats where the bot is added."""
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
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
    """Send a help message when the command /help is issued."""
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
        "/dollar - USDT/TRY ve USD/TRY kurlarını göster"
    )
    
    # Add admin commands if user is admin
    if is_admin:
        help_text += "\n\nAdmin komutları:\n/ban [kullanıcı_adı] - Kullanıcıyı banla\n/groupid - Mevcut sohbetin ID'sini göster"
    
    await update.message.reply_text(help_text)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from using the bot."""
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
    banned_users.add(username)
    
    await update.message.reply_text(f"@{username} kullanıcısı banlandı.")

async def get_btc_usd_price():
    """Fetch current BTC/USD price from Blink API."""
    try:
        logger.info("Fetching BTC/USD price from Blink API...")
        
        # Try a simpler query that's more likely to succeed
        simplified_query = """
        query {
          btcPrice {
            price {
              base
              offset
            }
            timestamp
          }
        }
        """
        
        response = requests.post(
            BLINK_API_URL,
            json={"query": simplified_query},
            timeout=10
        )
        
        # Log response details for debugging
        logger.info(f"Blink API response status: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Blink API request failed with status code {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        logger.info(f"Blink API response structure: {list(data.keys() if isinstance(data, dict) else [])}")
        
        # Check for errors in response
        if 'errors' in data:
            error_messages = [error.get('message', 'Unknown error') for error in data.get('errors', [])]
            error_message = "; ".join(error_messages)
            logger.error(f"Blink API returned errors: {error_message}")
            return None
            
        # Extract price from response
        if 'data' in data and data['data'] and 'btcPrice' in data['data']:
            price_data = data['data']['btcPrice']['price']
            base = float(price_data['base'])
            offset = int(price_data['offset'])
            # Calculate the proper price
            price = base * (10 ** -offset)
            logger.info(f"Successfully fetched BTC price from Blink: {price}")
            return price
        
        logger.error(f"Unexpected Blink API response format: {data}")
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Blink: {str(e)}")
        return None

async def get_btc_try_price():
    """Fetch current BTC/TRY price from BTCTurk API."""
    try:
        logger.info("Fetching BTC/TRY price from BTCTurk API...")
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        
        # Ensure we're dealing with JSON data
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            logger.error(f"BTCTurk API returned non-JSON response: {content_type}")
            logger.info(f"Response content: {response.text[:200]}...")
            return None
            
        data = response.json()
        logger.info(f"BTCTurk API response type: {type(data)}")
        
        # Check if the response has the expected structure
        if not isinstance(data, dict) or 'data' not in data:
            logger.error(f"BTCTurk API response missing 'data' field or has unexpected format: {type(data)}")
            return None
        
        # Find the BTCTRY pair
        for pair_data in data.get('data', []):
            if isinstance(pair_data, dict) and pair_data.get('pair') == 'BTCTRY':
                return float(pair_data.get('last', 0))
        
        logger.error("BTCTRY pair not found in the API response")
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/TRY price from BTCTurk: {str(e)}")
        return None

async def get_binance_btc_usd_price():
    """Fetch current BTC/USD price from Binance API."""
    try:
        response = requests.get(f"{BINANCE_API_URL}?symbol=BTCUSDT", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'price' in data:
            return float(data['price'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Binance: {str(e)}")
        return None

async def get_binance_btc_try_price():
    """Fetch current BTC/TRY price from Binance API."""
    try:
        response = requests.get(f"{BINANCE_API_URL}?symbol=BTCTRY", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'price' in data:
            return float(data['price'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/TRY price from Binance: {str(e)}")
        return None

async def get_kraken_btc_usd_price():
    """Fetch current BTC/USD price from Kraken API."""
    try:
        response = requests.get(f"{KRAKEN_API_URL}?pair=XBTUSDT", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'result' in data and 'XBTUSDT' in data['result']:
            # Get the last traded close price (first value in 'c' array)
            close_price = data['result']['XBTUSDT']['c'][0]
            return float(close_price)
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Kraken: {str(e)}")
        return None

async def get_paribu_btc_usd_price():
    """Fetch current BTC/USD price from Paribu API."""
    try:
        response = requests.get(PARIBU_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'BTC_USDT' in data and 'last' in data['BTC_USDT']:
            return float(data['BTC_USDT']['last'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Paribu: {str(e)}")
        return None

async def get_paribu_btc_try_price():
    """Fetch current BTC/TRY price from Paribu API."""
    try:
        response = requests.get(PARIBU_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'BTC_TL' in data and 'last' in data['BTC_TL']:
            return float(data['BTC_TL']['last'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/TRY price from Paribu: {str(e)}")
        return None

async def get_bitfinex_btc_usd_price():
    """Fetch current BTC/USD price from Bitfinex API."""
    try:
        response = requests.get(f"{BITFINEX_API_URL}/tBTCUSD", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # LAST_PRICE is at index 6 in the array
        if len(data) > 6:
            return float(data[6])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Bitfinex: {str(e)}")
        return None

async def get_bitfinex_btc_try_price():
    """Fetch current BTC/TRY price from Bitfinex API."""
    try:
        response = requests.get(f"{BITFINEX_API_URL}/tBTCTRY", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # LAST_PRICE is at index 6 in the array
        if len(data) > 6:
            return float(data[6])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/TRY price from Bitfinex: {str(e)}")
        return None

async def get_bitstamp_btc_usd_price():
    """Fetch current BTC/USD price from Bitstamp API."""
    try:
        response = requests.get(f"{BITSTAMP_API_URL}/btcusd/", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'last' in data:
            return float(data['last'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Bitstamp: {str(e)}")
        return None

async def get_coinbase_btc_usd_price():
    """Fetch current BTC/USD price from Coinbase API."""
    try:
        response = requests.get(f"{COINBASE_API_URL}/BTC-USD/spot", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and 'amount' in data['data']:
            return float(data['data']['amount'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Coinbase: {str(e)}")
        return None

async def get_okx_btc_usd_price():
    """Fetch current BTC/USD price from OKX API."""
    try:
        response = requests.get(f"{OKX_API_URL}?instId=BTC-USDT", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0 and 'last' in data['data'][0]:
            return float(data['data'][0]['last'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from OKX: {str(e)}")
        return None

async def get_bitflyer_btc_usd_price():
    """Fetch current BTC/USD price from Bitflyer API."""
    try:
        response = requests.get(f"{BITFLYER_API_URL}?product_code=BTC_USD", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'ltp' in data:
            return float(data['ltp'])
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Bitflyer: {str(e)}")
        return None

async def get_top_volume_pairs():
    """Fetch top 5 currency pairs with highest volume from BTCTurk API."""
    try:
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            # Calculate volume in denominator currency for each pair
            pairs_with_denominator_volume = []
            for pair_data in data['data']:
                try:
                    # Get the volume in numerator currency
                    volume = float(pair_data.get('volume', 0))
                    # Get the exchange rate
                    last_price = float(pair_data.get('last', 0))
                    
                    # Calculate volume in denominator currency
                    denominator_volume = volume * last_price
                    
                    # Create a new dictionary with the calculated volume
                    pair_with_denominator_volume = pair_data.copy()
                    pair_with_denominator_volume['denominator_volume'] = denominator_volume
                    
                    pairs_with_denominator_volume.append(pair_with_denominator_volume)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error calculating denominator volume for pair {pair_data.get('pair', 'unknown')}: {str(e)}")
                    continue
            
            # Sort pairs by denominator volume in descending order
            sorted_pairs = sorted(
                pairs_with_denominator_volume, 
                key=lambda x: x.get('denominator_volume', 0), 
                reverse=True
            )
            
            # Get top 5 pairs
            top_pairs = sorted_pairs[:5]
            
            return top_pairs
        
        return None
    except Exception as e:
        logger.error(f"Error fetching top volume pairs: {str(e)}")
        return None

async def get_usdt_try_rate():
    """Fetch USDT/TRY rate from BTCTurk API."""
    try:
        logger.info("Fetching USDT/TRY rate from BTCTurk API...")
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        
        # Ensure we're dealing with JSON data
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            logger.error(f"BTCTurk API returned non-JSON response: {content_type}")
            logger.info(f"Response content: {response.text[:200]}...")
            return None
            
        data = response.json()
        logger.info(f"BTCTurk API response type: {type(data)}")
        
        # Check if the response has the expected structure
        if not isinstance(data, dict) or 'data' not in data:
            logger.error(f"BTCTurk API response missing 'data' field or has unexpected format: {type(data)}")
            return None
        
        # Find the USDTTRY pair
        for pair_data in data.get('data', []):
            if isinstance(pair_data, dict) and pair_data.get('pair') == 'USDTTRY':
                rate = float(pair_data.get('last', 0))
                logger.info(f"Found USDT/TRY rate: {rate}")
                return rate
        
        logger.error("USDTTRY pair not found in BTCTurk API response")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching USDT/TRY rate: {str(e)}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data processing error fetching USDT/TRY rate: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching USDT/TRY rate: {str(e)}")
        return None

async def get_usd_try_rate():
    """Fetch USD/TRY rate from Yadio API."""
    try:
        logger.info("Fetching USD/TRY rate from Yadio API...")
        response = requests.get(YADIO_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Yadio API response: {data}")
        
        # The TRY rate is nested inside the 'USD' object
        if 'USD' in data and 'TRY' in data['USD']:
            rate = float(data['USD']['TRY'])
            logger.info(f"Found USD/TRY rate: {rate}")
            return rate
        
        logger.error("TRY rate not found in Yadio API response")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching USD/TRY rate: {str(e)}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data processing error fetching USD/TRY rate: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching USD/TRY rate: {str(e)}")
        return None

async def volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show top 5 currency pairs with highest volume."""
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "volume"):
        return
    
    try:
        top_pairs = await get_top_volume_pairs()
        
        if not top_pairs:
            await update.message.reply_text(
                "Üzgünüm, hacim bilgilerini alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        message = "📊 *En Yüksek Hacimli 5 Para Birimi Çifti*\n\n"
        
        # Find BTC/TRY pair and its rank
        btc_try_pair = None
        btc_try_rank = None
        
        for i, pair in enumerate(top_pairs, 1):
            pair_name = pair.get('pair', '')
            # Use the calculated denominator volume
            volume = float(pair.get('denominator_volume', 0))
            denominator_symbol = pair.get('denominatorSymbol', '')
            
            # Format volume without decimals
            formatted_volume = f"{int(volume):,}"
            
            message += f"{i}. *{pair_name}*: {formatted_volume} {denominator_symbol}\n"
            
            # Check if this is BTC/TRY
            if pair_name == 'BTCTRY':
                btc_try_pair = pair
                btc_try_rank = i
        
        # If BTC/TRY is not in top 5, add it separately
        if not btc_try_pair:
            # Find BTC/TRY in all pairs
            all_pairs = await get_all_pairs()
            if all_pairs:
                for i, pair in enumerate(all_pairs, 1):
                    if pair.get('pair') == 'BTCTRY':
                        btc_try_pair = pair
                        btc_try_rank = i
                        break
        
        # Add BTC/TRY information if it's not in top 5
        if btc_try_pair and btc_try_rank > 5:
            volume = float(btc_try_pair.get('denominator_volume', 0))
            denominator_symbol = btc_try_pair.get('denominatorSymbol', '')
            formatted_volume = f"{int(volume):,}"
            
            message += f"\n*BTCTRY*: {formatted_volume} {denominator_symbol} (Genel sıralama: #{btc_try_rank})"
        
        message += "\n_Veri kaynağı: BTCTurk_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in volume command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def get_all_pairs():
    """Fetch all currency pairs from BTCTurk API."""
    try:
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            # Calculate volume in denominator currency for each pair
            pairs_with_denominator_volume = []
            for pair_data in data['data']:
                try:
                    # Get the volume in numerator currency
                    volume = float(pair_data.get('volume', 0))
                    # Get the exchange rate
                    last_price = float(pair_data.get('last', 0))
                    
                    # Calculate volume in denominator currency
                    denominator_volume = volume * last_price
                    
                    # Create a new dictionary with the calculated volume
                    pair_with_denominator_volume = pair_data.copy()
                    pair_with_denominator_volume['denominator_volume'] = denominator_volume
                    
                    pairs_with_denominator_volume.append(pair_with_denominator_volume)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error calculating denominator volume for pair {pair_data.get('pair', 'unknown')}: {str(e)}")
                    continue
            
            # Sort pairs by denominator volume in descending order
            sorted_pairs = sorted(
                pairs_with_denominator_volume, 
                key=lambda x: x.get('denominator_volume', 0), 
                reverse=True
            )
            
            return sorted_pairs
        
        return None
    except Exception as e:
        logger.error(f"Error fetching all pairs: {str(e)}")
        return None

async def dollar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show USDT/TRY and USD/TRY exchange rates."""
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "dollar"):
        return
    
    try:
        await update.message.reply_text("Döviz kurları alınıyor, lütfen bekleyin...")
        
        # Get USDT/TRY rate from BTCTurk
        usdt_try_rate = await get_usdt_try_rate()
        
        # Get USD/TRY rate from Yadio
        usd_try_rate = await get_usd_try_rate()
        
        # Format the message based on available data
        message = "💵 *Güncel Dolar Kurları*\n\n"
        
        if usdt_try_rate is not None:
            message += f"*USDT/TRY:* ₺{usdt_try_rate:.2f}\n"
        else:
            message += "*USDT/TRY:* Veri alınamadı\n"
        
        if usd_try_rate is not None:
            message += f"*USD/TRY:* ₺{usd_try_rate:.2f}\n"
        else:
            message += "*USD/TRY:* Veri alınamadı\n"
        
        message += "\n_Veri kaynakları: BTCTurk, Yadio_"
        
        # Update the previous message with the results
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in dollar command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current BTC/USD and BTC/TRY prices from multiple sources."""
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
        btcturk_btc_try = await get_btc_try_price()
        binance_btc_try = await get_binance_btc_try_price()
        bitfinex_btc_try = await get_bitfinex_btc_try_price()
        paribu_btc_try = await get_paribu_btc_try_price()
        
        # Fetch BTC/USD prices from all sources
        blink_btc_usd = await get_btc_usd_price()
        binance_btc_usd = await get_binance_btc_usd_price()
        kraken_btc_usd = await get_kraken_btc_usd_price()
        paribu_btc_usd = await get_paribu_btc_usd_price()
        bitfinex_btc_usd = await get_bitfinex_btc_usd_price()
        bitstamp_btc_usd = await get_bitstamp_btc_usd_price()
        coinbase_btc_usd = await get_coinbase_btc_usd_price()
        okx_btc_usd = await get_okx_btc_usd_price()
        bitflyer_btc_usd = await get_bitflyer_btc_usd_price()
        
        # Count successful data fetches
        try_prices_count = sum(1 for p in [btcturk_btc_try, binance_btc_try, bitfinex_btc_try, paribu_btc_try] if p is not None)
        usd_prices_count = sum(1 for p in [blink_btc_usd, binance_btc_usd, kraken_btc_usd, paribu_btc_usd, 
                                          bitfinex_btc_usd, bitstamp_btc_usd, coinbase_btc_usd, okx_btc_usd, 
                                          bitflyer_btc_usd] if p is not None)
        
        # Check if we have any data to display
        if try_prices_count == 0 and usd_prices_count == 0:
            await update.message.reply_text(
                "Üzgünüm, hiçbir kaynaktan Bitcoin fiyat verisi alınamadı. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        message = "💰 *Güncel Bitcoin Fiyatları*\n\n"
        
        # BTC/TRY section
        if try_prices_count > 0:
            message += "*BTC/TRY*\n"
            
            if btcturk_btc_try is not None:
                message += f"BTCTurk: ₺{int(btcturk_btc_try):,}\n"
            
            if binance_btc_try is not None:
                message += f"Binance: ₺{int(binance_btc_try):,}\n"
            
            if bitfinex_btc_try is not None:
                message += f"Bitfinex: ₺{int(bitfinex_btc_try):,}\n"
            
            if paribu_btc_try is not None:
                message += f"Paribu: ₺{int(paribu_btc_try):,}\n"
            
            message += "\n"
        
        # BTC/USD section
        if usd_prices_count > 0:
            message += "*BTC/USD*\n"
            
            if binance_btc_usd is not None:
                message += f"Binance: ${int(binance_btc_usd):,}\n"
            
            if blink_btc_usd is not None:
                message += f"Blink: ${int(blink_btc_usd):,}\n"
            
            if bitstamp_btc_usd is not None:
                message += f"Bitstamp: ${int(bitstamp_btc_usd):,}\n"
            
            if bitfinex_btc_usd is not None:
                message += f"Bitfinex: ${int(bitfinex_btc_usd):,}\n"
            
            if coinbase_btc_usd is not None:
                message += f"Coinbase: ${int(coinbase_btc_usd):,}\n"
            
            if kraken_btc_usd is not None:
                message += f"Kraken: ${int(kraken_btc_usd):,}\n"
            
            if paribu_btc_usd is not None:
                message += f"Paribu: ${int(paribu_btc_usd):,}\n"
            
            if okx_btc_usd is not None:
                message += f"OKX: ${int(okx_btc_usd):,}\n"
            
            if bitflyer_btc_usd is not None:
                message += f"Bitflyer: ${int(bitflyer_btc_usd):,}\n"
            
            message += "\n"
        
        message += "_Veri kaynakları: Blink API, BTCTurk, Binance, Bitfinex, Kraken, Paribu, Bitstamp, Coinbase, OKX, Bitflyer_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in price command: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def convert_100lira(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert 100 TRY to satoshi and send the result."""
    # Check if user is banned
    if await is_banned(update):
        return
    
    # Check rate limit
    if await check_rate_limit(update, "100lira"):
        return
    
    try:
        # Fetch current exchange rate from BTCTurk
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        # Find the BTCTRY pair
        btc_try_data = None
        for pair_data in data.get('data', []):
            if pair_data.get('pair') == 'BTCTRY':
                btc_try_data = pair_data
                break
        
        if not btc_try_data:
            logger.error("BTCTRY pair not found in the API response")
            await update.message.reply_text(
                "Üzgünüm, BTC/TRY kurunu bulamadım. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        # Extract the last price
        btc_try_rate = float(btc_try_data.get('last', 0))
        
        if btc_try_rate <= 0:
            logger.error(f"Invalid exchange rate: {btc_try_rate}")
            await update.message.reply_text(
                "Üzgünüm, geçersiz bir kur aldım. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        # Calculate satoshi equivalent (1 BTC = 100,000,000 satoshi)
        lira_amount = 100
        btc_amount = lira_amount / btc_try_rate
        satoshi_amount = btc_amount * 100000000  # Convert BTC to satoshi
        
        # Format the response
        message = (
            f"💰 *100 Türk Lirası = {satoshi_amount:.0f} satoshi*\n\n"
            f"Kur: 1 BTC = ₺{int(btc_try_rate):,}\n"
            f"Veri kaynağı: BTCTurk\n"
            f"_Şu anda güncellendi_"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except requests.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, borsaya bağlanamadım. Lütfen daha sonra tekrar deneyin."
        )
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data processing error: {str(e)}")
        await update.message.reply_text(
            "Üzgünüm, borsa verilerini işlerken bir hata ile karşılaştım. Lütfen daha sonra tekrar deneyin."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        await update.message.reply_text(
            "Beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the ID of the current chat."""
    # Only admin can use this command
    if update.effective_user.username != ADMIN_USERNAME:
        return
    
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Private Chat"
    
    message = f"Chat ID: `{chat_id}`\nChat Title: {chat_title}"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def gimmecheese_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of sending Bitcoin via Lightning Network."""
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
    if BLINK_API_KEY == "YOUR_BLINK_API_KEY_HERE":
        await update.message.reply_text(
            "Blink API anahtarı ayarlanmamış. Lütfen config.py dosyasında BLINK_API_KEY değerini güncelleyin."
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
    """Process the Lightning Address and send Bitcoin."""
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
        wallet_data = await get_wallet_data()
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
        payment_result = await send_lightning_payment(lightning_address, 1000)
        
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

async def get_wallet_data():
    """Get wallet data from Blink API."""
    try:
        # GraphQL query to get wallet data
        query = """
        query Me {
          me {
            defaultAccount {
              wallets {
                id
                walletCurrency
                balance
              }
            }
          }
        }
        """
        
        # Make the API request
        response = requests.post(
            BLINK_API_URL,
            json={
                "query": query
            },
            headers={
                "X-API-KEY": BLINK_API_KEY
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract wallet data
        if 'data' in data and 'me' in data['data'] and 'defaultAccount' in data['data']['me']:
            return data['data']['me']['defaultAccount']['wallets']
        
        logger.error(f"Invalid wallet data response: {data}")
        return None
    
    except Exception as e:
        logger.error(f"Error getting wallet data: {str(e)}")
        return None

async def send_lightning_payment(lightning_address, amount_sats):
    """Send a payment to a Lightning Address."""
    try:
        # First, get the wallet data to find the BTC wallet ID
        wallet_data = await get_wallet_data()
        if not wallet_data:
            logger.error("Failed to get wallet data")
            return {"status": "ERROR", "errors": [{"message": "Failed to get wallet data"}]}
        
        # Find the BTC wallet
        btc_wallet = None
        for wallet in wallet_data:
            if wallet.get('walletCurrency') == 'BTC':
                btc_wallet = wallet
                break
        
        if not btc_wallet:
            logger.error("BTC wallet not found")
            return {"status": "ERROR", "errors": [{"message": "BTC wallet not found"}]}
        
        # Get the wallet ID
        wallet_id = btc_wallet.get('id')
        if not wallet_id:
            logger.error("Wallet ID not found")
            return {"status": "ERROR", "errors": [{"message": "Wallet ID not found"}]}
        
        # GraphQL mutation to send payment
        mutation = """
        mutation LnAddressPaymentSend($input: LnAddressPaymentSendInput!) {
          lnAddressPaymentSend(input: $input) {
            status
            errors {
              code
              message
              path
            }
          }
        }
        """
        
        # Variables for the mutation - include the walletId but NOT memo (which is not supported)
        variables = {
            "input": {
                "walletId": wallet_id,
                "lnAddress": lightning_address,
                "amount": str(amount_sats)  # Convert to string as per the example
            }
        }
        
        # Log the request for debugging
        logger.info(f"Sending Lightning payment to {lightning_address} for {amount_sats} sats")
        logger.info(f"Request variables: {variables}")
        
        # Make the API request
        response = requests.post(
            BLINK_API_URL,
            json={
                "query": mutation,
                "variables": variables
            },
            headers={
                "X-API-KEY": BLINK_API_KEY
            },
            timeout=30
        )
        
        # Log the response for debugging
        logger.info(f"Lightning payment response status: {response.status_code}")
        
        # Check if the response is valid JSON
        try:
            data = response.json()
            logger.info(f"Lightning payment response: {data}")
        except ValueError:
            logger.error(f"Invalid JSON response: {response.text}")
            return {"status": "ERROR", "errors": [{"message": "Invalid JSON response"}]}
        
        # Extract payment result
        if 'data' in data and data['data'] and 'lnAddressPaymentSend' in data['data']:
            return data['data']['lnAddressPaymentSend']
        
        # Handle case where data['data'] is None
        if 'errors' in data and data['errors']:
            error_messages = [error.get('message', 'Unknown error') for error in data['errors']]
            error_message = "; ".join(error_messages)
            logger.error(f"API returned errors: {error_message}")
            return {"status": "ERROR", "errors": [{"message": error_message}]}
        
        return {"status": "ERROR", "errors": [{"message": "Invalid API response"}]}
    
    except Exception as e:
        logger.error(f"Error sending lightning payment: {str(e)}")
        return {"status": "ERROR", "errors": [{"message": str(e)}]}

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END

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
    
    # Add conversation handler for gimmecheese command
    gimmecheese_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("gimmecheese", gimmecheese_command)],
        states={
            LIGHTNING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_lightning_address)]
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
    
    # Try to use job queue if available, otherwise use asyncio task
    try:
        if application.job_queue:
            application.job_queue.run_repeating(post_quote, interval=QUOTE_INTERVAL, first=10)
            logger.info("Using job queue for quote scheduling")
        else:
            # Create a task for quote scheduling
            asyncio.create_task(quote_scheduler(application))
            logger.info("Using asyncio task for quote scheduling")
    except Exception as e:
        logger.error(f"Error setting up quote scheduling: {str(e)}")
        # Fallback to asyncio task
        asyncio.create_task(quote_scheduler(application))
        logger.info("Using asyncio task for quote scheduling (fallback)")

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
