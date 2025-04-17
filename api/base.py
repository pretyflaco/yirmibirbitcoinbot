"""Base API module for making requests to external services.

This module provides common functionality for making API requests,
handling errors, and processing responses.
"""

import logging
import requests
from typing import Dict, Any, Optional, Union, List

# Set up logging
logger = logging.getLogger(__name__)

class BaseAPI:
    """Base class for API interactions.

    Provides common methods for making HTTP requests and handling responses.
    """

    @staticmethod
    def make_request(
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Make an HTTP request to the specified URL.

        Args:
            url: The URL to make the request to
            method: HTTP method (GET, POST, etc.)
            params: URL parameters
            data: Form data
            headers: HTTP headers
            json_data: JSON data for POST requests
            timeout: Request timeout in seconds

        Returns:
            The JSON response as a dictionary, or None if the request failed
        """
        try:
            logger.info(f"Making {method} request to {url}")

            # Make the request
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                json=json_data,
                timeout=timeout
            )

            # Log response status
            logger.info(f"Response status: {response.status_code}")

            # For debugging, log the first part of the response content
            if response.content:
                content_preview = response.content[:200].decode('utf-8', errors='replace')
                logger.debug(f"Response content preview: {content_preview}")

            # Raise an exception for 4xx/5xx status codes
            response.raise_for_status()

            # Parse JSON response
            if response.content:
                try:
                    json_response = response.json()
                    return json_response
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    logger.error(f"Response content: {response.content.decode('utf-8', errors='replace')}")
                    return None

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
