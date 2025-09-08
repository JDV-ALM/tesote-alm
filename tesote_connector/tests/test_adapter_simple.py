# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Simple unit tests for Tesote API Adapter that run without Odoo.
"""

# Import conftest first to set up Odoo mocks
from . import conftest

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import responses
import sys

class TestTesoteAdapterSimple:
    """Test Tesote API Adapter without Odoo dependencies."""
    
    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend record."""
        backend = Mock()
        backend.api_url = "https://test-1.miamibeachstart.com"
        backend.api_version = "v2"
        backend.api_token = "test_bearer_token_123"
        backend.rate_limit_calls = 200
        backend.rate_limit_period = 60
        return backend
    
    @pytest.fixture
    def adapter(self, mock_backend):
        """Create adapter instance with mock backend."""
        # Import after mocks are set up
        from ..components.adapter import TesoteAdapter
        return TesoteAdapter(mock_backend)
    
    def test_adapter_initialization(self, adapter, mock_backend):
        """Test that adapter initializes with correct configuration."""
        assert adapter.backend == mock_backend
        assert adapter.api_url == "https://test-1.miamibeachstart.com"
        assert adapter.api_token == "test_bearer_token_123"
    
    def test_session_headers(self, adapter):
        """Test that session has correct headers."""
        session = adapter.session
        assert session.headers['Authorization'] == "Bearer test_bearer_token_123"
        assert session.headers['Accept'] == "application/json"
        assert session.headers['Content-Type'] == "application/json"
        assert 'TesoteOdooConnector' in session.headers['User-Agent']
    
    def test_get_url_construction(self, adapter):
        """Test URL construction for API endpoints."""
        # Test known endpoints
        assert adapter._get_url('accounts') == "https://test-1.miamibeachstart.com/api/v2/accounts"
        assert adapter._get_url('status') == "https://test-1.miamibeachstart.com/api/v2/status"
        assert adapter._get_url('whoami') == "https://test-1.miamibeachstart.com/api/v2/whoami"
        
        # Test with parameters
        url = adapter._get_url('account_detail', account_id='123')
        assert url == "https://test-1.miamibeachstart.com/api/v2/accounts/123"
    
    @responses.activate
    def test_get_status(self, adapter):
        """Test checking API status."""
        # Setup mock response
        responses.add(
            responses.GET,
            "https://test-1.miamibeachstart.com/api/v2/status",
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
            "https://test-1.miamibeachstart.com/api/v2/whoami",
            json={
                "name": "Test Client",
                "environment": "Production"
            },
            status=200
        )
        
        # Execute
        result = adapter.get_whoami()
        
        # Assert
        assert result["name"] == "Test Client"
        assert result["environment"] == "Production"
    
    @responses.activate
    def test_list_accounts(self, adapter):
        """Test listing accounts with pagination."""
        # Setup mock response
        responses.add(
            responses.GET,
            "https://test-1.miamibeachstart.com/api/v2/accounts",
            json={
                "accounts": [
                    {"id": "acc-001", "name": "Checking"},
                    {"id": "acc-002", "name": "Savings"}
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
    def test_sync_transactions(self, adapter):
        """Test transaction sync with cursor."""
        # Setup mock response
        responses.add(
            responses.POST,
            "https://test-1.miamibeachstart.com/api/v2/transactions/sync",
            json={
                "added": [
                    {"transaction_id": "txn-001", "amount": 100}
                ],
                "modified": [],
                "removed": [],
                "next_cursor": "cursor-123",
                "has_more": False
            },
            status=200
        )
        
        # Execute - without cursor for initial sync
        result = adapter.sync_transactions(
            tesote_account_id="acc-001",
            cursor=None,
            count=100
        )
        
        # Assert
        assert len(result["added"]) == 1
        assert result["added"][0]["transaction_id"] == "txn-001"
        assert result["next_cursor"] == "cursor-123"
        assert result["has_more"] is False
    
    @responses.activate
    def test_rate_limit_error(self, adapter):
        """Test handling of rate limit errors."""
        # Setup mock response with 429 status
        responses.add(
            responses.GET,
            "https://test-1.miamibeachstart.com/api/v2/accounts",
            status=429,
            headers={"Retry-After": "60"},
            json={"error": "Rate limit exceeded"}
        )
        
        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            adapter.list_accounts()
        
        # Assert - NetworkRetryableError should be raised
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @responses.activate
    def test_authentication_error(self, adapter):
        """Test handling of authentication errors."""
        # Setup mock response with 401 status
        responses.add(
            responses.GET,
            "https://test-1.miamibeachstart.com/api/v2/accounts",
            status=401,
            json={"error": "Unauthorized", "message": "Invalid token"}
        )
        
        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            adapter.list_accounts()
        
        # Assert - UserError should be raised
        assert "401" in str(exc_info.value)
        assert "Invalid token" in str(exc_info.value)
    
    def test_sync_transactions_cursor_handling(self, adapter):
        """Test cursor handling in sync_transactions."""
        # Test that cursor is omitted when None
        with patch.object(adapter, '_request') as mock_request:
            mock_request.return_value = {
                "added": [],
                "modified": [],
                "removed": [],
                "next_cursor": "new-cursor",
                "has_more": False
            }
            
            # Call with no cursor
            adapter.sync_transactions("acc-001", cursor=None)
            
            # Check that cursor was not included in request data
            call_args = mock_request.call_args
            request_data = call_args[1]['data']
            assert 'cursor' not in request_data
            assert request_data['tesote_account_id'] == "acc-001"
            assert request_data['count'] == 100
    
    def test_sync_transactions_with_cursor(self, adapter):
        """Test sync_transactions with a valid cursor."""
        with patch.object(adapter, '_request') as mock_request:
            mock_request.return_value = {
                "added": [],
                "modified": [],
                "removed": [],
                "next_cursor": "newer-cursor",
                "has_more": False
            }
            
            # Call with a cursor
            adapter.sync_transactions("acc-001", cursor="existing-cursor")
            
            # Check that cursor was included
            call_args = mock_request.call_args
            request_data = call_args[1]['data']
            assert request_data['cursor'] == "existing-cursor"
            assert request_data['tesote_account_id'] == "acc-001"