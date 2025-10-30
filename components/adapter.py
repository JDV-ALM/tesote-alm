# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Tesote API Adapter.
Implements communication with Tesote API v2.0.0 following SOLID principles.
"""

import logging
from typing import Any
from urllib.parse import urljoin

import requests
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class NetworkRetryableError(Exception):
    """Exception for network errors that should be retried."""

    pass


class TesoteAdapter:
    """
    Adapter for Tesote API v2 communication.
    Handles authentication, rate limiting, and API calls.
    """

    # API v2 configuration
    API_VERSION = "v2"
    API_BASE_PATH = f"/api/{API_VERSION}/"

    # Rate limiting (per minute)
    RATE_LIMITS = {
        "standard": 200,
        "premium": 500,
        "enterprise": 1000,
    }

    # Endpoints
    ENDPOINTS = {
        "accounts": "accounts",
        "account_detail": "accounts/{account_id}",
        "transactions_sync": "accounts/{account_id}/transactions/sync",
        "status": "status",
        "whoami": "whoami",
    }

    def __init__(self, backend_record):
        """Initialize adapter with backend configuration."""
        self.backend = backend_record
        self.api_url = backend_record.api_url
        self.api_token = backend_record.api_token
        self._session = None

    @property
    def session(self):
        """Get or create requests session with authentication."""
        if not self._session:
            self._session = requests.Session()
            # Get module version from manifest
            module_version = getattr(self.backend, "_module_version", "18.0.1.0.0")
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self.api_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": f"TesoteOdooConnector/{module_version} (API/{self.API_VERSION}; Odoo/18.0; Python/requests)",
                }
            )
        return self._session

    def _get_url(self, endpoint: str, **kwargs) -> str:
        """Build full URL for API endpoint."""
        path = self.ENDPOINTS.get(endpoint, endpoint)
        if kwargs:
            path = path.format(**kwargs)
        return urljoin(self.api_url, self.API_BASE_PATH + path)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Make HTTP request to Tesote API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint name or path
            data: Request body data
            params: Query parameters
            **kwargs: Additional arguments for endpoint formatting

        Returns:
            API response as dictionary

        Raises:
            NetworkRetryableError: For temporary network issues
            UserError: For API errors
        """
        url = self._get_url(endpoint, **kwargs)

        try:
            _logger.info(f"API Request: {method} {url}")

            # Log request details for debugging
            if data:
                import json

                _logger.info(f"Request body: {data}")
                _logger.info(f"Request JSON: {json.dumps(data, indent=2)}")
            if params:
                _logger.info(f"Request params: {params}")

            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30,
            )

            # Log response for debugging errors
            _logger.info(f"Response status: {response.status_code}")
            if response.status_code >= 400:
                _logger.error(f"Error response body: {response.text}")

            # Log rate limit info
            if "X-RateLimit-Remaining" in response.headers:
                remaining = response.headers.get("X-RateLimit-Remaining")
                limit = response.headers.get("X-RateLimit-Limit")
                _logger.debug(f"Rate limit: {remaining}/{limit} requests remaining")

            # Handle errors
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise NetworkRetryableError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds"
                )

            if response.status_code >= 500:
                raise NetworkRetryableError(f"Server error {response.status_code}: {response.text}")

            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_code = error_data.get("error", "Unknown")
                error_message = error_data.get("message", response.text)

                # Check for historical sync forbidden error
                if response.status_code == 403 and (
                    "HISTORY_SYNC_FORBIDDEN" in str(error_code)
                    or "Historical sync is disabled" in str(error_message)
                ):
                    _logger.warning(
                        "Historical sync forbidden. Will skip historical data and sync from now."
                    )
                    # Return empty sync result to skip historical data
                    # The account will be marked as synced and future syncs will work
                    empty_result = {
                        "added": [],
                        "modified": [],
                        "removed": [],
                        "next_cursor": None,  # Will need to get a valid cursor on next sync
                        "has_more": False,
                    }
                    # Raise a special error to handle in the backend
                    raise UserError("HISTORY_SYNC_FORBIDDEN:SKIP")

                # Format the error message for display
                if error_message:
                    error_msg = error_message
                else:
                    error_msg = error_code or response.text

                raise UserError(f"API Error {response.status_code}: {error_msg}")

            return response.json() if response.text else {}

        except requests.exceptions.Timeout:
            raise NetworkRetryableError("Request timeout")
        except requests.exceptions.ConnectionError as e:
            raise NetworkRetryableError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Request error: {e}")
            raise UserError(f"API request failed: {e}")

    # API v2 Methods

    def get_status(self) -> dict[str, Any]:
        """Check API status."""
        return self._request("GET", "status")

    def get_whoami(self) -> dict[str, Any]:
        """Get client information."""
        return self._request("GET", "whoami")

    def list_accounts(self, page: int = 1, per_page: int = 100) -> dict[str, Any]:
        """
        List financial accounts.

        Args:
            page: Page number (1-based)
            per_page: Items per page (max 100)

        Returns:
            Dictionary with accounts list and pagination info
        """
        params = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        return self._request("GET", "accounts", params=params)

    def get_account(self, account_id: str) -> dict[str, Any]:
        """
        Get single account details.

        Args:
            account_id: Tesote account ID

        Returns:
            Account details dictionary
        """
        return self._request("GET", "account_detail", account_id=account_id)

    def sync_transactions(
        self, tesote_account_id: str, cursor: str | None = None, count: int = 100
    ) -> dict[str, Any]:
        """
        Sync transactions using v2 nested endpoint (RESTful).

        Uses: POST /api/v2/accounts/{accountId}/transactions/sync

        This is the recommended endpoint that follows REST conventions with
        the account ID in the URL path (not the request body).

        Args:
            tesote_account_id: The Tesote account ID to sync
            cursor: Sync cursor (None/null for initial sync, or cursor UUID from previous sync)
            count: Maximum number of transactions to return (max 500)

        Returns:
            Dictionary containing:
                - added: List of new transactions
                - modified: List of updated transactions
                - removed: List of deleted transaction IDs
                - next_cursor: Cursor for next sync
                - has_more: Boolean indicating more data available
        """
        # Build request data (account_id now in URL path, not body)
        data = {
            "count": min(count, 500),  # API max is 500
        }

        # Only include cursor if it's provided and not None
        # For initial sync, omit cursor entirely (don't send null)
        if cursor is not None:
            # Skip if it's our special marker
            if cursor != "synced_without_history":
                data["cursor"] = cursor

        _logger.info(
            f"=== SYNC TRANSACTIONS REQUEST ===\n"
            f"Endpoint: POST /api/v2/accounts/{tesote_account_id}/transactions/sync\n"
            f"Cursor: {cursor!r} (type: {type(cursor).__name__})\n"
            f"Count: {data['count']}\n"
            f"Request body: {data}"
        )

        result = self._request("POST", "transactions_sync", data=data, account_id=tesote_account_id)

        # Log sync statistics
        added = len(result.get("added", []))
        modified = len(result.get("modified", []))
        removed = len(result.get("removed", []))

        _logger.info(
            f"Sync result: {added} added, {modified} modified, {removed} removed transactions"
        )

        return result

    # Alias methods for compatibility with tests
    def get_account_detail(self, account_id: str) -> dict:
        """Alias for get_account for test compatibility."""
        return self.get_account(account_id)

    def get_transaction_detail(self, transaction_id: str) -> dict:
        """Get transaction details by ID."""
        return self._request("GET", f"transactions/{transaction_id}")

    def process_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process incoming webhook notification.

        Args:
            webhook_data: Webhook payload from Tesote

        Returns:
            Processing result
        """
        event_type = webhook_data.get("event")
        _logger.info(f"Processing webhook event: {event_type}")

        # Webhook events: accounts.created, accounts.updated, sync.updates_available
        if event_type == "sync.updates_available":
            # Trigger sync for specified accounts
            account_ids = webhook_data.get("data", {}).get("account_ids", [])
            return {
                "action": "sync_accounts",
                "account_ids": account_ids,
            }

        return {"status": "processed"}
