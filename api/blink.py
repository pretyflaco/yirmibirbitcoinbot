"""Blink API module for fetching Bitcoin price data and sending Lightning payments.

This module provides functions to interact with the Blink API
for retrieving Bitcoin price data and sending Lightning payments.
"""

import logging
from typing import Dict, Any, Optional, List

from api.base import BaseAPI
from config import BLINK_API_URL, BLINK_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

class BlinkAPI(BaseAPI):
    """Blink API client for fetching Bitcoin price data and sending Lightning payments."""

    @classmethod
    async def get_btc_usd_price(cls) -> Optional[float]:
        """Fetch current BTC/USD price from Blink API.

        Returns:
            The BTC/USD price as a float, or None if the request failed
        """
        try:
            logger.info("Fetching BTC/USD price from Blink API...")

            # Use the correct query and variables
            query = """
            query ExampleQuery($range: PriceGraphRange!) {
              btcPriceList(range: $range) {
                price {
                  base
                  currencyUnit
                  formattedAmount
                  offset
                }
                timestamp
              }
            }
            """

            variables = {
                "range": "ONE_DAY"
            }

            # Make the API request
            response_data = cls.make_request(
                url=BLINK_API_URL,
                method="POST",
                json_data={
                    "query": query,
                    "variables": variables
                }
            )

            # Log response details for debugging
            logger.info(f"Blink API response status: {response_data is not None}")

            # Check for errors in response
            if response_data is None:
                logger.error("Blink API returned None response")
                return None

            if 'errors' in response_data:
                error_messages = [error.get('message', 'Unknown error') for error in response_data.get('errors', [])]
                error_message = "; ".join(error_messages)
                logger.error(f"Blink API returned errors: {error_message}")
                return None

            if 'data' not in response_data:
                logger.error(f"Blink API response missing 'data' field: {response_data}")
                return None

            if 'btcPriceList' not in response_data['data'] or not response_data['data']['btcPriceList']:
                logger.error(f"Blink API response missing or empty 'btcPriceList': {response_data['data']}")
                return None

            # Extract price from response
            try:
                # Get all prices and sort by timestamp to get the most recent one
                price_list = response_data['data']['btcPriceList']

                # Log the number of prices received
                logger.info(f"Received {len(price_list)} price points from Blink API")

                # Sort by timestamp in descending order (most recent first)
                sorted_prices = sorted(price_list, key=lambda x: int(x.get('timestamp', 0)), reverse=True)

                # Log the timestamps for debugging
                timestamps = [p.get('timestamp') for p in sorted_prices[:5]]
                logger.info(f"First few timestamps after sorting: {timestamps}")

                # Use the most recent price (first after sorting)
                price_data = sorted_prices[0]['price']
                base = float(price_data['base'])
                offset = int(price_data['offset'])

                # Calculate the proper price
                # The Blink API returns prices that are 100x the actual value, so we need to divide by 100
                # This is because the API returns prices in cents (1/100 of a dollar)
                price = (base * (10 ** -offset)) / 100
                logger.info(f"Successfully fetched BTC price from Blink: {price}")
                return price

            except (KeyError, IndexError, ValueError, TypeError) as e:
                logger.error(f"Error extracting price from Blink API response: {str(e)}")
                logger.error(f"Unexpected Blink API response format: {response_data}")
                return None

        except Exception as e:
            logger.error(f"Error fetching BTC/USD price from Blink: {str(e)}")
            return None

    @classmethod
    async def get_wallet_data(cls) -> Optional[List[Dict[str, Any]]]:
        """Get wallet data from Blink API.

        Returns:
            List of wallet data dictionaries, or None if the request failed
        """
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
            response_data = cls.make_request(
                url=BLINK_API_URL,
                method="POST",
                json_data={"query": query},
                headers={"X-API-KEY": BLINK_API_KEY}
            )

            # Extract wallet data
            if 'data' in response_data and 'me' in response_data['data'] and 'defaultAccount' in response_data['data']['me']:
                return response_data['data']['me']['defaultAccount']['wallets']

            logger.error(f"Invalid wallet data response: {response_data}")
            return None

        except Exception as e:
            logger.error(f"Error getting wallet data: {str(e)}")
            return None

    @classmethod
    async def send_lightning_payment(cls, lightning_address: str, amount_sats: int) -> Dict[str, Any]:
        """Send a payment to a Lightning Address.

        Args:
            lightning_address: The Lightning Address to send to
            amount_sats: The amount to send in satoshis

        Returns:
            Dictionary with payment status and any errors
        """
        try:
            # First, get the wallet data to find the BTC wallet ID
            wallet_data = await cls.get_wallet_data()
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
            response_data = cls.make_request(
                url=BLINK_API_URL,
                method="POST",
                json_data={
                    "query": mutation,
                    "variables": variables
                },
                headers={"X-API-KEY": BLINK_API_KEY},
                timeout=30
            )

            # Extract payment result
            if 'data' in response_data and response_data['data'] and 'lnAddressPaymentSend' in response_data['data']:
                return response_data['data']['lnAddressPaymentSend']

            # Handle case where data['data'] is None
            if 'errors' in response_data and response_data['errors']:
                error_messages = [error.get('message', 'Unknown error') for error in response_data['errors']]
                error_message = "; ".join(error_messages)
                logger.error(f"API returned errors: {error_message}")
                return {"status": "ERROR", "errors": [{"message": error_message}]}

            return {"status": "ERROR", "errors": [{"message": "Invalid API response"}]}

        except Exception as e:
            logger.error(f"Error sending lightning payment: {str(e)}")
            return {"status": "ERROR", "errors": [{"message": str(e)}]}

    @classmethod
    async def pay_lightning_invoice(cls, payment_request: str) -> Dict[str, Any]:
        """Pay a Lightning Network invoice (Bolt11).

        Args:
            payment_request: The Bolt11 invoice to pay

        Returns:
            Dictionary with payment status and any errors
        """
        try:
            # First, get the wallet data to find the BTC wallet ID
            wallet_data = await cls.get_wallet_data()
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

            # GraphQL mutation to pay invoice
            mutation = """
            mutation LnInvoicePaymentSend($input: LnInvoicePaymentInput!) {
              lnInvoicePaymentSend(input: $input) {
                status
                errors {
                  message
                  path
                  code
                }
              }
            }
            """

            # Variables for the mutation
            variables = {
                "input": {
                    "walletId": wallet_id,
                    "paymentRequest": payment_request
                }
            }

            # Log the request for debugging
            logger.info(f"Paying Lightning invoice: {payment_request}")
            logger.info(f"Request variables: {variables}")

            # Make the API request
            response_data = cls.make_request(
                url=BLINK_API_URL,
                method="POST",
                json_data={
                    "query": mutation,
                    "variables": variables
                },
                headers={"X-API-KEY": BLINK_API_KEY},
                timeout=30
            )

            # Extract payment result
            if 'data' in response_data and response_data['data'] and 'lnInvoicePaymentSend' in response_data['data']:
                return response_data['data']['lnInvoicePaymentSend']

            # Handle case where data['data'] is None
            if 'errors' in response_data and response_data['errors']:
                error_messages = [error.get('message', 'Unknown error') for error in response_data['errors']]
                error_message = "; ".join(error_messages)
                logger.error(f"API returned errors: {error_message}")
                return {"status": "ERROR", "errors": [{"message": error_message}]}

            return {"status": "ERROR", "errors": [{"message": "Invalid API response"}]}

        except Exception as e:
            logger.error(f"Error paying Lightning invoice: {str(e)}")
            return {"status": "ERROR", "errors": [{"message": str(e)}]}

    @classmethod
    async def pay_no_amount_lightning_invoice(cls, payment_request: str, amount_sats: int) -> Dict[str, Any]:
        """Pay a Lightning Network invoice with no amount (Bolt11).

        Args:
            payment_request: The Bolt11 invoice to pay
            amount_sats: The amount to pay in satoshis

        Returns:
            Dictionary with payment status and any errors
        """
        try:
            # First, get the wallet data to find the BTC wallet ID
            wallet_data = await cls.get_wallet_data()
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

            # GraphQL mutation to pay no-amount invoice
            mutation = """
            mutation LnNoAmountInvoicePaymentSend($input: LnNoAmountInvoicePaymentInput!) {
              lnNoAmountInvoicePaymentSend(input: $input) {
                status
                errors {
                  message
                  path
                  code
                }
              }
            }
            """

            # Variables for the mutation
            variables = {
                "input": {
                    "walletId": wallet_id,
                    "paymentRequest": payment_request,
                    "amount": str(amount_sats)
                }
            }

            # Log the request for debugging
            logger.info(f"Paying Lightning no-amount invoice: {payment_request} with amount: {amount_sats} sats")
            logger.info(f"Request variables: {variables}")

            # Make the API request
            response_data = cls.make_request(
                url=BLINK_API_URL,
                method="POST",
                json_data={
                    "query": mutation,
                    "variables": variables
                },
                headers={"X-API-KEY": BLINK_API_KEY},
                timeout=30
            )

            # Extract payment result
            if 'data' in response_data and response_data['data'] and 'lnNoAmountInvoicePaymentSend' in response_data['data']:
                return response_data['data']['lnNoAmountInvoicePaymentSend']

            # Handle case where data['data'] is None
            if 'errors' in response_data and response_data['errors']:
                error_messages = [error.get('message', 'Unknown error') for error in response_data['errors']]
                error_message = "; ".join(error_messages)
                logger.error(f"API returned errors: {error_message}")
                return {"status": "ERROR", "errors": [{"message": error_message}]}

            return {"status": "ERROR", "errors": [{"message": "Invalid API response"}]}

        except Exception as e:
            logger.error(f"Error paying Lightning no-amount invoice: {str(e)}")
            return {"status": "ERROR", "errors": [{"message": str(e)}]}

    @classmethod
    def detect_payment_type(cls, input_text: str) -> Dict[str, Any]:
        """Detect the type of payment from user input.

        Args:
            input_text: The user input text

        Returns:
            Dictionary with payment type and additional info
        """
        # Check if it's a Lightning Address
        if '@' in input_text and not input_text.startswith('ln'):
            return {
                "type": "lightning_address",
                "value": input_text.strip()
            }

        # Check if it's a Bolt11 invoice
        if input_text.lower().startswith('lnbc'):
            # Try to extract the amount from the invoice
            try:
                # The amount is encoded after the 'lnbc' prefix
                # For example: lnbc21n... means 21 satoshis (not 210)
                # lnbc1m... means 100,000 satoshis (10^5)

                # Extract the amount part (numeric part after 'lnbc')
                amount_part = ''
                for char in input_text[4:]:  # Skip 'lnbc'
                    if char.isdigit():
                        amount_part += char
                    else:
                        break

                # Get the multiplier character (the letter after the amount)
                multiplier_char = input_text[4 + len(amount_part):4 + len(amount_part) + 1]

                # If there's just 1 digit followed by 'p', it's a no-amount invoice
                if len(amount_part) == 1 and multiplier_char == 'p':
                    return {
                        "type": "bolt11_no_amount",
                        "value": input_text.strip()
                    }

                # Parse the amount correctly based on the multiplier
                amount = int(amount_part)
                if multiplier_char == 'n':
                    # Nano-bitcoin (0.000000001 BTC = 0.1 satoshi)
                    # For invoices with 'n', the amount is exactly the number before 'n'
                    # e.g., lnbc21n = 21 sats (not 210)
                    amount = amount
                elif multiplier_char == 'p':
                    # Pico-bitcoin (0.000000000001 BTC = 0.0001 satoshi)
                    # For invoices with 'p', it's typically a no-amount invoice
                    return {
                        "type": "bolt11_no_amount",
                        "value": input_text.strip()
                    }
                elif multiplier_char == 'u':
                    # Micro-bitcoin (0.000001 BTC = 100 satoshis)
                    # For invoices with 'u', multiply by 100
                    amount = amount * 100
                elif multiplier_char == 'm':
                    # Milli-bitcoin (0.001 BTC = 100,000 satoshis)
                    # For invoices with 'm', multiply by 100,000
                    amount = amount * 100000

                # Log the detected amount for debugging
                logger.info(f"Detected amount {amount} sats from invoice {input_text[:15]}...")

                return {
                    "type": "bolt11_with_amount",
                    "value": input_text.strip(),
                    "amount": amount
                }
            except Exception as e:
                logger.error(f"Error parsing Bolt11 invoice amount: {str(e)}")
                # If we can't parse the amount, assume it's a no-amount invoice
                return {
                    "type": "bolt11_unknown",
                    "value": input_text.strip()
                }

        # Unknown payment type
        return {
            "type": "unknown",
            "value": input_text.strip()
        }