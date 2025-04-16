"""Formatting utility for the Telegram bot.

This module provides functions to format messages and data
for display in Telegram messages.
"""

import logging
from typing import Dict, Any, Optional, List, Union

# Set up logging
logger = logging.getLogger(__name__)

def format_price_message(
    btc_try_prices: Dict[str, Optional[float]],
    btc_usd_prices: Dict[str, Optional[float]]
) -> str:
    """Format Bitcoin price data into a readable message.
    
    Args:
        btc_try_prices: Dictionary of BTC/TRY prices by exchange
        btc_usd_prices: Dictionary of BTC/USD prices by exchange
        
    Returns:
        Formatted message string
    """
    # Count successful data fetches
    try_prices_count = sum(1 for p in btc_try_prices.values() if p is not None)
    usd_prices_count = sum(1 for p in btc_usd_prices.values() if p is not None)
    
    # Check if we have any data to display
    if try_prices_count == 0 and usd_prices_count == 0:
        return "Üzgünüm, hiçbir kaynaktan Bitcoin fiyat verisi alınamadı. Lütfen daha sonra tekrar deneyin."
    
    message = "💰 *Güncel Bitcoin Fiyatları*\n\n"
    
    # BTC/TRY section
    if try_prices_count > 0:
        message += "*BTC/TRY*\n"
        
        for exchange, price in btc_try_prices.items():
            if price is not None:
                message += f"{exchange}: ₺{int(price):,}\n"
        
        message += "\n"
    
    # BTC/USD section
    if usd_prices_count > 0:
        message += "*BTC/USD*\n"
        
        for exchange, price in btc_usd_prices.items():
            if price is not None:
                message += f"{exchange}: ${int(price):,}\n"
        
        message += "\n"
    
    message += "_Veri kaynakları: Blink API, BTCTurk, Binance, Bitfinex, Kraken, Paribu, Bitstamp, Coinbase, OKX, Bitflyer_"
    
    return message

def format_volume_message(top_pairs: List[Dict[str, Any]], btc_try_pair: Optional[Dict[str, Any]] = None, btc_try_rank: Optional[int] = None) -> str:
    """Format volume data into a readable message.
    
    Args:
        top_pairs: List of top volume pairs
        btc_try_pair: BTC/TRY pair data if available
        btc_try_rank: Rank of BTC/TRY pair if available
        
    Returns:
        Formatted message string
    """
    if not top_pairs:
        return "Üzgünüm, hacim bilgilerini alırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
    
    message = "📊 *En Yüksek Hacimli 5 Para Birimi Çifti*\n\n"
    
    # Add top pairs
    for i, pair in enumerate(top_pairs, 1):
        pair_name = pair.get('pair', '')
        # Use the calculated denominator volume
        volume = float(pair.get('denominator_volume', 0))
        denominator_symbol = pair.get('denominatorSymbol', '')
        
        # Format volume without decimals
        formatted_volume = f"{int(volume):,}"
        
        message += f"{i}. *{pair_name}*: {formatted_volume} {denominator_symbol}\n"
    
    # Add BTC/TRY information if it's not in top 5
    if btc_try_pair and btc_try_rank and btc_try_rank > 5:
        volume = float(btc_try_pair.get('denominator_volume', 0))
        denominator_symbol = btc_try_pair.get('denominatorSymbol', '')
        formatted_volume = f"{int(volume):,}"
        
        message += f"\n*BTCTRY*: {formatted_volume} {denominator_symbol} (Genel sıralama: #{btc_try_rank})"
    
    message += "\n_Veri kaynağı: BTCTurk_"
    
    return message

def format_dollar_message(usdt_try_rate: Optional[float], usd_try_rate: Optional[float]) -> str:
    """Format dollar exchange rate data into a readable message.
    
    Args:
        usdt_try_rate: USDT/TRY exchange rate
        usd_try_rate: USD/TRY exchange rate
        
    Returns:
        Formatted message string
    """
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
    
    return message

def format_100lira_message(btc_try_rate: float) -> str:
    """Format 100 TRY to satoshi conversion into a readable message.
    
    Args:
        btc_try_rate: BTC/TRY exchange rate
        
    Returns:
        Formatted message string
    """
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
    
    return message
