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

            # Log the response for debugging
            logger.info(f"Invoice creation response: {response_data}")

            # Check if the response has the expected structure
            if isinstance(response_data, dict):
                # The payment_hash field indicates success
                if "payment_hash" in response_data:
                    logger.info(f"Successfully created invoice: {response_data['payment_hash']}")

                    # Extract the payment_request (Bolt11 invoice)
                    payment_request = response_data.get('payment_request', '')
                    if not payment_request:
                        # Try alternate field names that might contain the invoice
                        payment_request = response_data.get('bolt11', '')

                    if payment_request:
                        logger.info(f"Payment request: {payment_request[:30]}...")
                        return {
                            "status": "SUCCESS",
                            "invoice": {
                                "payment_hash": response_data.get('payment_hash', ''),
                                "payment_request": payment_request
                            }
                        }
                    else:
                        logger.error("Payment request not found in response")
                        return {
                            "status": "ERROR",
                            "errors": [{"message": "Payment request not found in response"}]
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

    @classmethod
    async def check_payment_status(cls, wallet_key: str, payment_hash: str) -> Dict[str, Any]:
        """Check if a payment has been received.

        Args:
            wallet_key: The wallet's inkey or admin key
            payment_hash: The payment hash to check

        Returns:
            Dictionary with payment status or error information
        """
        try:
            # Endpoint for checking payment status
            url = f"{LNBITS_API_URL}/payments/{payment_hash}"

            # Headers with the wallet key
            headers = {
                "accept": "application/json",
                "X-API-KEY": wallet_key,
                "Content-type": "application/json"
            }

            logger.info(f"Checking payment status for hash: {payment_hash}")

            # Make the API request
            response_data = cls.make_request(
                url=url,
                method="GET",
                headers=headers,
                timeout=30
            )

            # Log the response for debugging
            logger.info(f"Payment status response: {response_data}")

            # Check if the response has the expected structure
            if isinstance(response_data, dict) and "paid" in response_data:
                paid = response_data.get("paid", False)
                logger.info(f"Payment status for {payment_hash}: {'Paid' if paid else 'Not paid'}")

                return {
                    "status": "SUCCESS",
                    "paid": paid
                }

            # Handle error response
            logger.error(f"Unexpected response format from LNBits API: {response_data}")
            return {
                "status": "ERROR",
                "errors": [{"message": "Invalid API response format"}]
            }

        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return {
                "status": "ERROR",
                "errors": [{"message": str(e)}]
            }

    @classmethod
    async def get_wallet_balance(cls, wallet_key: str) -> Dict[str, Any]:
        """Get the current balance of a wallet.

        Args:
            wallet_key: The wallet's admin key or inkey

        Returns:
            Dictionary with wallet balance or error information
        """
        try:
            # Endpoint for getting wallet info
            url = f"{LNBITS_API_URL}/wallet"

            # Headers with the wallet key
            headers = {
                "accept": "application/json",
                "X-API-KEY": wallet_key,
                "Content-Type": "application/json"
            }

            logger.info(f"Fetching wallet balance")

            # Make the API request
            response_data = cls.make_request(
                url=url,
                method="GET",
                headers=headers,
                timeout=30
            )

            # Log the response for debugging
            logger.info(f"Wallet info response: {response_data}")

            # Check if the response has the expected structure
            if isinstance(response_data, dict) and "balance" in response_data:
                # Convert from millisatoshis to satoshis
                balance_msat = response_data.get("balance", 0)
                balance_sat = balance_msat // 1000

                logger.info(f"Wallet balance: {balance_sat} sats")

                return {
                    "status": "SUCCESS",
                    "balance_sat": balance_sat,
                    "balance_msat": balance_msat
                }

            # Handle error response
            logger.error(f"Unexpected response format from LNBits API: {response_data}")
            return {
                "status": "ERROR",
                "errors": [{"message": "Invalid API response format"}]
            }

        except Exception as e:
            logger.error(f"Error fetching wallet balance: {str(e)}")
            return {
                "status": "ERROR",
                "errors": [{"message": str(e)}]
            }

    # End of class

        Args:
            wallet_key: The wallet's admin key or inkey

        Returns:
            Dictionary with wallet balance or error information
        """
        try:
            # Endpoint for getting wallet info
            url = f"{LNBITS_API_URL}/wallet"

            # Headers with the wallet key
            headers = {
                "accept": "application/json",
                "X-API-KEY": wallet_key,
                "Content-Type": "application/json"
            }

            logger.info(f"Fetching wallet balance")

            # Make the API request
            response_data = cls.make_request(
                url=url,
                method="GET",
                headers=headers,
                timeout=30
            )

            # Log the response for debugging
            logger.info(f"Wallet info response: {response_data}")

            # Check if the response has the expected structure
            if isinstance(response_data, dict) and "balance" in response_data:
                # Convert from millisatoshis to satoshis
                balance_msat = response_data.get("balance", 0)
                balance_sat = balance_msat // 1000

                logger.info(f"Wallet balance: {balance_sat} sats")

                return {
                    "status": "SUCCESS",
                    "balance_sat": balance_sat,
                    "balance_msat": balance_msat
                }

            # Handle error response
            logger.error(f"Unexpected response format from LNBits API: {response_data}")
            return {
                "status": "ERROR",
                "errors": [{"message": "Invalid API response format"}]
            }

        except Exception as e:
            logger.error(f"Error fetching wallet balance: {str(e)}")
            return {
                "status": "ERROR",
                "errors": [{"message": str(e)}]
            }