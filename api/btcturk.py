"""BTCTurk API module for fetching cryptocurrency data.

This module provides functions to interact with the BTCTurk API
for retrieving cryptocurrency prices, trading pairs, and volume data.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from api.base import BaseAPI
from config import BTCTURK_API_TICKER_URL

# Set up logging
logger = logging.getLogger(__name__)

class BTCTurkAPI(BaseAPI):
    """BTCTurk API client for fetching cryptocurrency data."""
    
    @classmethod
    async def get_btc_try_price(cls) -> Optional[float]:
        """Fetch current BTC/TRY price from BTCTurk API.
        
        Returns:
            The BTC/TRY price as a float, or None if the request failed
        """
        try:
            logger.info("Fetching BTC/TRY price from BTCTurk API...")
            
            # Make the API request
            response_data = cls.make_request(BTCTURK_API_TICKER_URL)
            
            # Check if the response has the expected structure
            if not isinstance(response_data, dict) or 'data' not in response_data:
                logger.error(f"BTCTurk API response has unexpected format: {response_data}")
                return None
            
            # Debug: Print the first few pairs in the response
            pairs_found = []
            for i, pair_data in enumerate(response_data['data'][:5]):
                if isinstance(pair_data, dict):
                    pair = pair_data.get('pair', 'unknown')
                    last_price = pair_data.get('last', 'unknown')
                    pairs_found.append(f"{pair}:{last_price}")
            
            logger.info(f"First few pairs in BTCTurk response: {pairs_found}")
            
            # Find the BTCTRY pair
            for pair_data in response_data['data']:
                if isinstance(pair_data, dict) and pair_data.get('pair') == 'BTCTRY':
                    price = float(pair_data['last'])
                    logger.info(f"Found BTC/TRY price: {price}")
                    return price
            
            logger.error("BTCTRY pair not found in the API response")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching BTC/TRY price from BTCTurk: {str(e)}")
            return None
    
    @classmethod
    async def get_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from BTCTurk API.
        
        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            logger.info("Fetching BTC/USD price from BTCTurk API...")
            
            # Make the API request
            response_data = cls.make_request(BTCTURK_API_TICKER_URL)
            
            # Check if the response has the expected structure
            if not isinstance(response_data, dict) or 'data' not in response_data:
                logger.error(f"BTCTurk API response has unexpected format: {response_data}")
                return None
            
            # Find the BTCUSDT pair
            for pair_data in response_data['data']:
                if isinstance(pair_data, dict) and pair_data.get('pair') == 'BTCUSDT':
                    price = float(pair_data['last'])
                    logger.info(f"Found BTC/USD price from BTCTurk: {price}")
                    return price
            
            logger.error("BTCUSDT pair not found in the API response")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from BTCTurk: {str(e)}")
            return None
    
    @classmethod
    async def get_usdt_try_rate(cls) -> Optional[float]:
        """Fetch USDT/TRY rate from BTCTurk API.
        
        Returns:
            The USDT/TRY rate as a float, or None if the request failed
        """
        try:
            logger.info("Fetching USDT/TRY rate from BTCTurk API...")
            
            # Make the API request
            response_data = cls.make_request(BTCTURK_API_TICKER_URL)
            
            # Check if the response has the expected structure
            if not isinstance(response_data, dict) or 'data' not in response_data or not response_data.get('success', False):
                logger.error(f"BTCTurk API response has unexpected format: {response_data}")
                return None
            
            # Find the USDTTRY pair
            for pair_data in response_data.get('data', []):
                if isinstance(pair_data, dict) and pair_data.get('pair') == 'USDTTRY':
                    rate = float(pair_data.get('last', 0))
                    logger.info(f"Found USDT/TRY rate: {rate}")
                    return rate
            
            logger.error("USDTTRY pair not found in BTCTurk API response")
            # Debug: Log some of the pairs that were found
            pairs = [p.get('pair') for p in response_data.get('data', [])[:5] if isinstance(p, dict)]
            logger.info(f"First few pairs found: {pairs}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching USDT/TRY rate: {str(e)}")
            return None
    
    @classmethod
    async def get_top_volume_pairs(cls, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Fetch top currency pairs with highest volume from BTCTurk API.
        
        Args:
            limit: Number of top pairs to return
            
        Returns:
            List of dictionaries containing pair data, or None if the request failed
        """
        try:
            # Make the API request
            response_data = cls.make_request(BTCTURK_API_TICKER_URL)
            
            if 'data' in response_data:
                # Calculate volume in denominator currency for each pair
                pairs_with_denominator_volume = []
                for pair_data in response_data['data']:
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
                
                # Get top pairs
                top_pairs = sorted_pairs[:limit]
                
                return top_pairs
            
            return None
        except Exception as e:
            logger.error(f"Error fetching top volume pairs: {str(e)}")
            return None
    
    @classmethod
    async def get_all_pairs(cls) -> Optional[List[Dict[str, Any]]]:
        """Fetch all currency pairs from BTCTurk API.
        
        Returns:
            List of dictionaries containing pair data, or None if the request failed
        """
        try:
            # Make the API request
            response_data = cls.make_request(BTCTURK_API_TICKER_URL)
            
            if 'data' in response_data:
                # Calculate volume in denominator currency for each pair
                pairs_with_denominator_volume = []
                for pair_data in response_data['data']:
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
