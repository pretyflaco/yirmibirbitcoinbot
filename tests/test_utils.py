"""Tests for the utility modules.

This module contains unit tests for the utility modules.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.formatting import (
    format_price_message,
    format_volume_message,
    format_dollar_message,
    format_100lira_message
)

class TestFormatting(unittest.TestCase):
    """Test cases for the formatting utility functions."""
    
    def test_format_price_message(self):
        """Test formatting price message."""
        # Test data
        btc_try_prices = {
            "BTCTurk": 1000000,
            "Binance": 1010000,
            "Bitfinex": None,
            "Paribu": 990000
        }
        
        btc_usd_prices = {
            "BTCTurk": 45000,
            "Binance": 45100,
            "Blink": 44900,
            "Bitstamp": None,
            "Bitfinex": 45200,
            "Coinbase": 45050,
            "Kraken": None,
            "Paribu": 44800,
            "OKX": 45150,
            "Bitflyer": 45300
        }
        
        # Format the message
        message = format_price_message(btc_try_prices, btc_usd_prices)
        
        # Verify the result
        self.assertIn("BTC/TRY", message)
        self.assertIn("BTC/USD", message)
        self.assertIn("BTCTurk: ₺1,000,000", message)
        self.assertIn("Binance: $45,100", message)
        self.assertNotIn("Bitfinex: ₺", message)  # None values should be skipped
        self.assertNotIn("Bitstamp: $", message)  # None values should be skipped
    
    def test_format_volume_message(self):
        """Test formatting volume message."""
        # Test data
        top_pairs = [
            {"pair": "BTCUSDT", "denominatorSymbol": "USDT", "denominator_volume": 10000000},
            {"pair": "ETHUSDT", "denominatorSymbol": "USDT", "denominator_volume": 5000000},
            {"pair": "XRPUSDT", "denominatorSymbol": "USDT", "denominator_volume": 2000000},
            {"pair": "LTCUSDT", "denominatorSymbol": "USDT", "denominator_volume": 1000000},
            {"pair": "DOGEUSDT", "denominatorSymbol": "USDT", "denominator_volume": 500000}
        ]
        
        btc_try_pair = {"pair": "BTCTRY", "denominatorSymbol": "TRY", "denominator_volume": 300000}
        btc_try_rank = 8
        
        # Format the message
        message = format_volume_message(top_pairs, btc_try_pair, btc_try_rank)
        
        # Verify the result
        self.assertIn("En Yüksek Hacimli 5 Para Birimi Çifti", message)
        self.assertIn("1. *BTCUSDT*: 10,000,000 USDT", message)
        self.assertIn("BTCTRY", message)
        self.assertIn("Genel sıralama: #8", message)
    
    def test_format_dollar_message(self):
        """Test formatting dollar message."""
        # Test data
        usdt_try_rate = 30.5
        usd_try_rate = 30.2
        
        # Format the message
        message = format_dollar_message(usdt_try_rate, usd_try_rate)
        
        # Verify the result
        self.assertIn("Güncel Dolar Kurları", message)
        self.assertIn("USDT/TRY: ₺30.50", message)
        self.assertIn("USD/TRY: ₺30.20", message)
    
    def test_format_100lira_message(self):
        """Test formatting 100 lira message."""
        # Test data
        btc_try_rate = 1000000
        
        # Format the message
        message = format_100lira_message(btc_try_rate)
        
        # Verify the result
        self.assertIn("100 Türk Lirası = 10000 satoshi", message)
        self.assertIn("Kur: 1 BTC = ₺1,000,000", message)

if __name__ == '__main__':
    unittest.main()
