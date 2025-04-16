"""Tests for the API modules.

This module contains unit tests for the API client modules.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.base import BaseAPI
from api.btcturk import BTCTurkAPI
from api.blink import BlinkAPI
from api.exchanges import ExchangesAPI

class TestBaseAPI(unittest.TestCase):
    """Test cases for the BaseAPI class."""
    
    @patch('api.base.requests.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": [{"pair": "BTCTRY", "last": 1000000}]}
        mock_response.content = b'{"success": true, "data": [{"pair": "BTCTRY", "last": 1000000}]}'
        mock_request.return_value = mock_response
        
        # Make the request
        result = BaseAPI.make_request("https://api.example.com")
        
        # Verify the result
        self.assertEqual(result, {"success": True, "data": [{"pair": "BTCTRY", "last": 1000000}]})
        
        # Verify the request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.example.com",
            params=None,
            data=None,
            headers=None,
            json=None,
            timeout=10
        )
    
    @patch('api.base.requests.request')
    def test_make_request_http_error(self, mock_request):
        """Test API request with HTTP error."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_request.return_value = mock_response
        
        # Make the request
        result = BaseAPI.make_request("https://api.example.com")
        
        # Verify the result
        self.assertIsNone(result)

class TestBTCTurkAPI(unittest.TestCase):
    """Test cases for the BTCTurkAPI class."""
    
    @patch('api.btcturk.BaseAPI.make_request')
    async def test_get_btc_try_price(self, mock_make_request):
        """Test getting BTC/TRY price from BTCTurk API."""
        # Mock the response
        mock_make_request.return_value = {
            "success": True,
            "data": [
                {"pair": "BTCTRY", "last": 1000000},
                {"pair": "ETHTRY", "last": 50000}
            ]
        }
        
        # Get the price
        price = await BTCTurkAPI.get_btc_try_price()
        
        # Verify the result
        self.assertEqual(price, 1000000)
    
    @patch('api.btcturk.BaseAPI.make_request')
    async def test_get_btc_try_price_no_data(self, mock_make_request):
        """Test getting BTC/TRY price with no data."""
        # Mock the response
        mock_make_request.return_value = {"success": False}
        
        # Get the price
        price = await BTCTurkAPI.get_btc_try_price()
        
        # Verify the result
        self.assertIsNone(price)

class TestBlinkAPI(unittest.TestCase):
    """Test cases for the BlinkAPI class."""
    
    @patch('api.blink.BaseAPI.make_request')
    async def test_get_btc_usd_price(self, mock_make_request):
        """Test getting BTC/USD price from Blink API."""
        # Mock the response
        mock_make_request.return_value = {
            "data": {
                "btcPriceList": [
                    {
                        "price": {
                            "base": 4500000,
                            "offset": 2,
                            "currencyUnit": "CENTS"
                        }
                    }
                ]
            }
        }
        
        # Get the price
        price = await BlinkAPI.get_btc_usd_price()
        
        # Verify the result
        self.assertEqual(price, 45000.0)
    
    @patch('api.blink.BaseAPI.make_request')
    async def test_get_btc_usd_price_error(self, mock_make_request):
        """Test getting BTC/USD price with error."""
        # Mock the response
        mock_make_request.return_value = {
            "errors": [
                {"message": "API error"}
            ]
        }
        
        # Get the price
        price = await BlinkAPI.get_btc_usd_price()
        
        # Verify the result
        self.assertIsNone(price)

class TestExchangesAPI(unittest.TestCase):
    """Test cases for the ExchangesAPI class."""
    
    @patch('api.exchanges.BaseAPI.make_request')
    async def test_get_binance_btc_usd_price(self, mock_make_request):
        """Test getting BTC/USD price from Binance API."""
        # Mock the response
        mock_make_request.return_value = {"price": "45000.00"}
        
        # Get the price
        price = await ExchangesAPI.get_binance_btc_usd_price()
        
        # Verify the result
        self.assertEqual(price, 45000.0)
    
    @patch('api.exchanges.BaseAPI.make_request')
    async def test_get_usd_try_rate(self, mock_make_request):
        """Test getting USD/TRY rate from Yadio API."""
        # Mock the response
        mock_make_request.return_value = {"USD": {"TRY": 30.5}}
        
        # Get the rate
        rate = await ExchangesAPI.get_usd_try_rate()
        
        # Verify the result
        self.assertEqual(rate, 30.5)

if __name__ == '__main__':
    unittest.main()
