"""API module for fetching data from various cryptocurrency exchanges.

This module provides functions to interact with multiple cryptocurrency exchange APIs
for retrieving Bitcoin price data in USD and TRY.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from api.base import BaseAPI
from config import (
    BINANCE_API_URL,
    KRAKEN_API_URL,
    PARIBU_API_URL,
    BITFINEX_API_URL,
    BITSTAMP_API_URL,
    COINBASE_API_URL,
    OKX_API_URL,
    BITFLYER_API_URL,
    YADIO_API_URL
)

# Set up logging
logger = logging.getLogger(__name__)

class ExchangesAPI(BaseAPI):
    """API client for fetching data from various cryptocurrency exchanges."""
    
    @classmethod
    async def get_binance_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Binance API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(
                url=f"{BINANCE_API_URL}",
                params={"symbol": "BTCUSDT"}
            )
            
            if response_data and 'price' in response_data:
                return float(response_data['price'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Binance: {str(e)}")
            return None
    
    @classmethod
    async def get_binance_btc_try_price(cls) -> Optional[float]:
        """Fetch current BTC/TRY price from Binance API.
        
        Returns:
            The BTC/TRY price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(
                url=f"{BINANCE_API_URL}",
                params={"symbol": "BTCTRY"}
            )
            
            if response_data and 'price' in response_data:
                return float(response_data['price'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/TRY price from Binance: {str(e)}")
            return None
    
    @classmethod
    async def get_kraken_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Kraken API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(
                url=f"{KRAKEN_API_URL}",
                params={"pair": "XBTUSDT"}
            )
            
            if response_data and 'result' in response_data and 'XBTUSDT' in response_data['result']:
                # Get the last traded close price (first value in 'c' array)
                close_price = response_data['result']['XBTUSDT']['c'][0]
                return float(close_price)
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Kraken: {str(e)}")
            return None
    
    @classmethod
    async def get_paribu_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Paribu API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(PARIBU_API_URL)
            
            if response_data and 'BTC_USDT' in response_data and 'last' in response_data['BTC_USDT']:
                return float(response_data['BTC_USDT']['last'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Paribu: {str(e)}")
            return None
    
    @classmethod
    async def get_paribu_btc_try_price(cls) -> Optional[float]:
        """Fetch current BTC/TRY price from Paribu API.
        
        Returns:
            The BTC/TRY price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(PARIBU_API_URL)
            
            if response_data and 'BTC_TL' in response_data and 'last' in response_data['BTC_TL']:
                return float(response_data['BTC_TL']['last'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/TRY price from Paribu: {str(e)}")
            return None
    
    @classmethod
    async def get_bitfinex_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Bitfinex API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(f"{BITFINEX_API_URL}/tBTCUSD")
            
            # LAST_PRICE is at index 6 in the array
            if response_data and len(response_data) > 6:
                return float(response_data[6])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Bitfinex: {str(e)}")
            return None
    
    @classmethod
    async def get_bitfinex_btc_try_price(cls) -> Optional[float]:
        """Fetch current BTC/TRY price from Bitfinex API.
        
        Returns:
            The BTC/TRY price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(f"{BITFINEX_API_URL}/tBTCTRY")
            
            # LAST_PRICE is at index 6 in the array
            if response_data and len(response_data) > 6:
                return float(response_data[6])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/TRY price from Bitfinex: {str(e)}")
            return None
    
    @classmethod
    async def get_bitstamp_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Bitstamp API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(f"{BITSTAMP_API_URL}/btcusd/")
            
            if response_data and 'last' in response_data:
                return float(response_data['last'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Bitstamp: {str(e)}")
            return None
    
    @classmethod
    async def get_coinbase_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Coinbase API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(f"{COINBASE_API_URL}/BTC-USD/spot")
            
            if response_data and 'data' in response_data and 'amount' in response_data['data']:
                return float(response_data['data']['amount'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Coinbase: {str(e)}")
            return None
    
    @classmethod
    async def get_okx_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from OKX API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(
                url=f"{OKX_API_URL}",
                params={"instId": "BTC-USDT"}
            )
            
            if (response_data and 'data' in response_data and 
                len(response_data['data']) > 0 and 'last' in response_data['data'][0]):
                return float(response_data['data'][0]['last'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from OKX: {str(e)}")
            return None
    
    @classmethod
    async def get_bitflyer_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Bitflyer API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            response_data = cls.make_request(
                url=f"{BITFLYER_API_URL}",
                params={"product_code": "BTC_USD"}
            )
            
            if response_data and 'ltp' in response_data:
                return float(response_data['ltp'])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Bitflyer: {str(e)}")
            return None
    
    @classmethod
    async def get_usd_try_rate(cls) -> Optional[float]:
        """Fetch USD/TRY rate from Yadio API.
        
        Returns:
            The USD/TRY rate as a float, or None if the request failed
        """
        try:
            logger.info("Fetching USD/TRY rate from Yadio API...")
            response_data = cls.make_request(YADIO_API_URL)
            
            logger.info(f"Yadio API response: {response_data}")
            
            # The TRY rate is nested inside the 'USD' object
            if response_data and 'USD' in response_data and 'TRY' in response_data['USD']:
                rate = float(response_data['USD']['TRY'])
                logger.info(f"Found USD/TRY rate: {rate}")
                return rate
            
            logger.error("TRY rate not found in Yadio API response")
            return None
        except Exception as e:
            logger.error(f"Error fetching USD/TRY rate: {str(e)}")
            return None
