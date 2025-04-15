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
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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
    BLINK_PRICE_VARIABLES
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

# Store for rate limiting
command_last_used = {}
banned_users = set()
quotes = []
last_quote_time = {}
replied_to_messages = set()

# Load quotes from JSON file
def load_quotes():
    global quotes
    try:
        with open('quotes.json', 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        logger.info(f"Loaded {len(quotes)} Satoshi quotes")
    except Exception as e:
        logger.error(f"Error loading quotes: {str(e)}")
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

async def post_quote(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Post a random Satoshi quote to all groups."""
    quote = get_random_quote()
    if not quote:
        logger.error("No quotes available to post")
        return
    
    # Get all chats where the bot is a member
    for chat_id in context.bot_data.get('quote_chats', set()):
        try:
            # Check if it's time to post in this chat
            current_time = time.time()
            last_time = last_quote_time.get(chat_id, 0)
            
            if current_time - last_time >= QUOTE_INTERVAL:
                # Post the quote
                message = f"💬 *Satoshi Nakamoto*\n\n{quote['text']}"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                # Update the last quote time
                last_quote_time[chat_id] = current_time
                logger.info(f"Posted quote to chat {chat_id}")
        except Exception as e:
            logger.error(f"Error posting quote to chat {chat_id}: {str(e)}")

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
        if 'quote_chats' not in context.bot_data:
            context.bot_data['quote_chats'] = set()
        context.bot_data['quote_chats'].add(chat_id)
        logger.info(f"Bot added to chat {chat_id}, now tracking for quote posts")

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
    
    await update.message.reply_text(
        "Türk Lirası'nı Bitcoin satoshi'ye çevirmenize yardımcı olabilirim.\n\n"
        "Kullanılabilir komutlar:\n"
        "/100lira - 100 TL'yi anlık kur ile satoshi'ye çevir\n"
        "/price - Güncel BTC/USD ve BTC/TRY kurlarını göster\n"
        "/volume - En yüksek hacimli 5 para birimi çiftini göster\n"
        "/dollar - USDT/TRY ve USD/TRY kurlarını göster"
    )

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
        response = requests.post(
            BLINK_API_URL,
            json={
                "query": BLINK_PRICE_QUERY,
                "variables": BLINK_PRICE_VARIABLES
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and 'btcPriceList' in data['data'] and data['data']['btcPriceList']:
            # Get the most recent price (last item in the array)
            price_data = data['data']['btcPriceList'][-1]['price']
            base = float(price_data['base'])
            offset = int(price_data['offset'])
            # Fix the 10x multiplier issue by dividing by 100
            return (base / (10 ** offset)) / 100
        
        return None
    except Exception as e:
        logger.error(f"Error fetching BTC/USD price from Blink: {str(e)}")
        return None

async def get_btc_try_price():
    """Fetch current BTC/TRY price from BTCTurk API."""
    try:
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for pair_data in data.get('data', []):
            if pair_data.get('pair') == 'BTCTRY':
                return float(pair_data.get('last', 0))
        
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
        data = response.json()
        
        logger.info(f"BTCTurk API response: {data}")
        
        for pair_data in data.get('data', []):
            if pair_data.get('pair') == 'USDTTRY':
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
        usdt_try_rate = await get_usdt_try_rate()
        usd_try_rate = await get_usd_try_rate()
        
        if usdt_try_rate is None or usd_try_rate is None:
            await update.message.reply_text(
                "Üzgünüm, döviz kurlarını alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
            return
        
        message = (
            f"💵 *Güncel Dolar Kurları*\n\n"
            f"*USDT/TRY:* ₺{usdt_try_rate:.2f}\n"
            f"*USD/TRY:* ₺{usd_try_rate:.2f}\n\n"
            f"_Veri kaynakları: BTCTurk, Yadio_"
        )
        
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
        
        message = "💰 *Güncel Bitcoin Fiyatları*\n\n"
        
        # BTC/TRY section
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
        
        message += "\n_Veri kaynakları: Blink API, BTCTurk, Binance, Bitfinex, Kraken, Paribu, Bitstamp, Coinbase, OKX, Bitflyer_"
        
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

def main() -> None:
    """Start the bot."""
    # Load quotes
    load_quotes()
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("100lira", convert_100lira))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("volume", volume_command))
    application.add_handler(CommandHandler("dollar", dollar_command))
    application.add_handler(CommandHandler("ban", ban_command))
    
    # Add handlers for tracking new chats and handling source requests
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_chat))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, handle_source_request))
    
    # Add job for posting quotes every 12 hours
    application.job_queue.run_repeating(post_quote, interval=QUOTE_INTERVAL, first=10)

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
