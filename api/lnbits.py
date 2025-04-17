import logging
from typing import Dict, Any, Optional
import json

from api.base import BaseAPI
from config import LNBITS_API_URL, LNBITS_API_KEY

logger = logging.getLogger(__name__)

class LNBitsAPI(BaseAPI):
    """API client for LNBits."""

    @classmethod
    async def create_wallet(cls, user_id: str) -> Dict[str, Any]:
        """Create a new wallet for a user.

        Args:
            user_id: The Telegram user ID to use as the wallet name

        Returns:
            Dictionary with wallet details or error information
        """
        try:
            # Endpoint for creating a wallet
            url = f"{LNBITS_API_URL}/wallet"

            # Request body
            data = {
                "name": f"telegram_{user_id}"
            }

            # Headers
            headers = {
                "accept": "application/json",
                "X-API-KEY": LNBITS_API_KEY,
                "Content-Type": "application/json"
            }

            logger.info(f"Creating LNBits wallet for user {user_id}")

            # Make the API request
            response_data = cls.make_request(
                url=url,
                method="POST",
                json_data=data,
                headers=headers,
                timeout=30
            )

            # Check if the response has the expected structure
            if isinstance(response_data, dict) and "id" in response_data:
                logger.info(f"Successfully created wallet for user {user_id}: {response_data['id']}")
                return {
                    "status": "SUCCESS",
                    "wallet": response_data
                }

            # Handle error response
            logger.error(f"Unexpected response format from LNBits API: {response_data}")
            return {
                "status": "ERROR",
                "errors": [{"message": "Invalid API response format"}]
            }

        except Exception as e:
            logger.error(f"Error creating LNBits wallet: {str(e)}")
            return {
                "status": "ERROR",
                "errors": [{"message": str(e)}]
            }

    @classmethod
    async def create_invoice(cls, wallet_key: str, amount: int, memo: str = "Yirmibir Bitcoin Bot") -> Dict[str, Any]:
        """Create a new invoice (Bolt11) for receiving funds.

        Args:
            wallet_key: The wallet's inkey to use for creating the invoice
            amount: The amount in satoshis
            memo: Description for the invoice

        Returns:
            Dictionary with invoice details or error information
        """
        try:
            # Endpoint for creating a payment
            url = f"{LNBITS_API_URL}/payments"

            # Request body
            data = {
                "out": False,  # False for receiving funds
                "amount": amount,
                "unit": "sat",
                "memo": memo,
                "internal": False
            }

            # Headers with the wallet key
            headers = {
                "accept": "application/json",
                "X-API-KEY": wallet_key,  # Use the wallet's inkey
                "Content-Type": "application/json"
            }

            logger.info(f"Creating invoice for {amount} sats with memo: {memo}")

            # Make the API request
            response_data = cls.make_request(
                url=url,
                method="POST",
                json_data=data,
                headers=headers,
                timeout=30
            )

            # Check if the response has the expected structure
            if isinstance(response_data, dict) and "payment_hash" in response_data:
                logger.info(f"Successfully created invoice: {response_data['payment_hash']}")
                return {
                    "status": "SUCCESS",
                    "invoice": response_data
                }

            # Handle error response
            logger.error(f"Unexpected response format from LNBits API: {response_data}")
            return {
                "status": "ERROR",
                "errors": [{"message": "Invalid API response format"}]
            }

        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            return {
                "status": "ERROR",
                "errors": [{"message": str(e)}]
            }
