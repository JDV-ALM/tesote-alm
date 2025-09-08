# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Test Tesote API Adapter following TDD principles.
Tests are written first, then implementation follows.
"""

# Import conftest first to set up Odoo mocks
from . import conftest

import json
from unittest.mock import Mock, patch, MagicMock
import responses
import pytest
from datetime import datetime
from freezegun import freeze_time


class TestTesoteAdapter:
    """Test Tesote API Adapter with TDD approach."""
    
    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend record."""
        backend = Mock()
        backend.api_url = "https://staging.tesote.com"
        backend.api_version = "v2"
        backend.api_token = "test_bearer_token_123"
        backend.rate_limit_calls = 100
        backend.rate_limit_period = 60
        return backend
    
    @pytest.fixture
    def adapter(self, mock_backend):
        """Create adapter instance with mock backend."""
        from ..components.adapter import TesoteAdapter
        return TesoteAdapter(mock_backend)
    
    def test_adapter_initialization(self, adapter, mock_backend):
        """Test that adapter initializes with correct configuration."""
        assert adapter.backend == mock_backend
        assert adapter.api_url == "https://staging.tesote.com"
        assert adapter.api_token == "test_bearer_token_123"
    
    @responses.activate
    def test_get_status(self, adapter):
        """Test checking API status."""
        # Setup mock response
        responses.add(
            responses.GET,
            "https://staging.tesote.com/api/v2/status",
            json={"status": "ok"},
            status=200
        )
        
        # Execute
        result = adapter.get_status()
        
        # Assert
        assert result["status"] == "ok"
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_get_whoami(self, adapter):
        """Test fetching client information."""
        # Setup mock response
        responses.add(
            responses.GET,
            "https://staging.tesote.com/api/v2/whoami",
            json={
                "name": "Test Corporation",
                "environment": "Production"
            },
            status=200
        )
        
        # Execute
        result = adapter.get_whoami()
        
        # Assert
        assert result["name"] == "Test Corporation"
        assert result["environment"] == "Production"
    
    @responses.activate
    def test_list_accounts(self, adapter):
        """Test listing accounts with pagination."""
        # Setup mock response
        responses.add(
            responses.GET,
            "https://staging.tesote.com/api/v2/accounts",
            json={
                "accounts": [
                    {
                        "id": "acc-001",
                        "name": "Checking Account"
                    },
                    {
                        "id": "acc-002", 
                        "name": "Savings Account"
                    }
                ],
                "page": 1,
                "per_page": 100,
                "total": 2
            },
            status=200
        )
        
        # Execute
        result = adapter.list_accounts(page=1, per_page=100)
        
        # Assert
        assert len(result["accounts"]) == 2
        assert result["accounts"][0]["id"] == "acc-001"
        assert result["page"] == 1
        
    @responses.activate
    def test_get_account_detail(self, adapter):
        """Test fetching a single account by ID."""
        account_id = "ff8c37c0-b538-4074-936c-bca2943a9773"
        
        # Setup mock response
        responses.add(
            responses.GET,
            f"https://staging.tesote.com/api/v2/accounts/{account_id}",
            json={
                "id": account_id,
                "name": "Banco Santander (...4521)",
                "bank_name": "Santander",
                "tesote_created_at": "2024-12-01T09:15:30-05:00",
                "tesote_updated_at": "2024-12-15T10:30:00-05:00"
            },
            status=200
        )
        
        # Execute
        result = adapter.get_account_detail(account_id)
        
        # Assert
        assert result["id"] == account_id
        assert result["name"] == "Banco Santander (...4521)"
        assert result["bank_name"] == "Santander"
    
    @responses.activate
    def test_sync_transactions(self, adapter):
        """Test syncing transactions with cursor."""
        account_id = "acc-001"
        
        # Setup mock response
        responses.add(
            responses.POST,
            "https://staging.tesote.com/api/v2/transactions/sync",
            json={
                "added": [
                    {
                        "transaction_id": "txn-001",
                        "amount": -50.00,
                        "description": "Coffee Shop"
                    }
                ],
                "modified": [],
                "removed": [],
                "next_cursor": "cursor-123",
                "has_more": False
            },
            status=200
        )
        
        # Execute
        result = adapter.sync_transactions(
            tesote_account_id=account_id,
            cursor="now",
            count=100
        )
        
        # Assert
        assert len(result["added"]) == 1
        assert result["added"][0]["transaction_id"] == "txn-001"
        assert result["next_cursor"] == "cursor-123"
        assert result["has_more"] is False
    
    @responses.activate
    def test_get_transaction_detail(self, adapter):
        """Test fetching a single transaction by ID."""
        transaction_id = "fe46b712-ad15-46f8-b231-5e266f2d4ff9"
        
        # Setup mock response
        responses.add(
            responses.GET,
            f"https://staging.tesote.com/api/v2/transactions/{transaction_id}",
            json={
                "transaction_id": transaction_id,
                "status": "completed",
                "amount": 100.00,
                "description": "Amazon Purchase",
                "tesote_imported_at": "2024-12-14T14:35:22-05:00",
                "tesote_updated_at": "2024-12-15T09:45:18-05:00"
            },
            status=200
        )
        
        # Execute
        result = adapter.get_transaction_detail(transaction_id)
        
        # Assert
        assert result["transaction_id"] == transaction_id
        assert result["status"] == "completed"
        assert result["amount"] == 100.00
    
    @responses.activate
    def test_rate_limit_handling(self, adapter):
        """Test handling of rate limit responses."""
        # Setup mock response with 429 status
        responses.add(
            responses.GET,
            "https://staging.tesote.com/api/v2/accounts",
            status=429,
            headers={"Retry-After": "30"},
            json={"error": "Rate limit exceeded"}
        )
        
        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            adapter.list_accounts()
        
        # Assert
        assert "429" in str(exc_info.value) or "rate limit" in str(exc_info.value).lower()
    
    @responses.activate  
    def test_authentication_error(self, adapter):
        """Test handling of authentication errors."""
        # Setup mock response with 401 status
        responses.add(
            responses.GET,
            "https://staging.tesote.com/api/v2/accounts",
            status=401,
            json={"error": "Invalid or missing bearer token"}
        )
        
        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            adapter.list_accounts()
        
        # Assert
        assert "401" in str(exc_info.value)
    
    def test_pagination_methods(self, adapter):
        """Test that pagination methods exist."""
        # Since we're mocking, we'll just test the method exists
        assert hasattr(adapter, 'list_accounts')
        assert hasattr(adapter, 'sync_transactions')
    
    def test_rate_limit_attributes(self, adapter):
        """Test that adapter has rate limit attributes."""
        # Check that adapter has backend with rate limit settings
        assert hasattr(adapter, 'backend')
        assert hasattr(adapter.backend, 'rate_limit_calls')
        assert adapter.backend.rate_limit_calls == 100