#!/usr/bin/env python3
# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Standalone test for Tesote API Adapter that runs without Odoo.
This test extracts just the adapter logic without Odoo dependencies.
"""

import json
import sys
from unittest.mock import Mock, patch
import responses
import requests

# Simple adapter class without Odoo dependencies
class TesoteAdapterStandalone:
    """Standalone version of Tesote API Adapter for testing."""
    
    API_VERSION = 'v2'
    API_BASE_PATH = f'/api/{API_VERSION}/'
    
    ENDPOINTS = {
        'accounts': 'accounts',
        'account_detail': 'accounts/{account_id}',
        'transactions_sync': 'transactions/sync',
        'status': 'status',
        'whoami': 'whoami',
    }
    
    def __init__(self, api_url, api_token):
        """Initialize with API credentials."""
        self.api_url = api_url
        self.api_token = api_token
        self._session = None
    
    @property
    def session(self):
        """Get or create requests session with authentication."""
        if not self._session:
            self._session = requests.Session()
            self._session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': f'TesoteOdooConnector/{self.API_VERSION}',
            })
        return self._session
    
    def _get_url(self, endpoint, **kwargs):
        """Build full URL for API endpoint."""
        from urllib.parse import urljoin
        path = self.ENDPOINTS.get(endpoint, endpoint)
        if kwargs:
            path = path.format(**kwargs)
        return urljoin(self.api_url, self.API_BASE_PATH + path)
    
    def _request(self, method, endpoint, data=None, params=None, **kwargs):
        """Make HTTP request to Tesote API."""
        url = self._get_url(endpoint, **kwargs)
        
        print(f"API Request: {method} {url}")
        if data:
            print(f"Request body: {json.dumps(data, indent=2)}")
        
        response = self.session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            timeout=30,
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code >= 400:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', response.text)
            raise Exception(f"API Error {response.status_code}: {error_msg}")
        
        return response.json() if response.text else {}
    
    def get_status(self):
        """Check API status."""
        return self._request('GET', 'status')
    
    def get_whoami(self):
        """Get client information."""
        return self._request('GET', 'whoami')
    
    def list_accounts(self, page=1, per_page=100):
        """List financial accounts."""
        params = {
            'page': page,
            'per_page': min(per_page, 100),
        }
        return self._request('GET', 'accounts', params=params)
    
    def sync_transactions(self, tesote_account_id, cursor=None, count=100):
        """Sync transactions using v2 sync endpoint."""
        data = {
            'tesote_account_id': tesote_account_id,
            'count': min(count, 500),
        }
        
        # Only include cursor if provided
        if cursor is not None and cursor != "synced_without_history":
            data['cursor'] = cursor
        
        print(f"=== SYNC TRANSACTIONS REQUEST ===")
        print(f"Account ID: {tesote_account_id}")
        print(f"Cursor: {cursor!r}")
        print(f"Full request data: {data}")
        
        result = self._request('POST', 'transactions_sync', data=data)
        
        # Log sync statistics
        added = len(result.get('added', []))
        modified = len(result.get('modified', []))
        removed = len(result.get('removed', []))
        
        print(f"Sync result: {added} added, {modified} modified, {removed} removed")
        
        return result


def test_adapter_basic():
    """Test basic adapter functionality."""
    print("\n=== Testing Tesote API Adapter ===\n")
    
    # Create adapter
    adapter = TesoteAdapterStandalone(
        api_url="https://test-1.miamibeachstart.com",
        api_token="test_token_123"
    )
    
    # Test URL construction
    print("Testing URL construction...")
    assert adapter._get_url('status') == "https://test-1.miamibeachstart.com/api/v2/status"
    assert adapter._get_url('accounts') == "https://test-1.miamibeachstart.com/api/v2/accounts"
    assert adapter._get_url('account_detail', account_id='123') == "https://test-1.miamibeachstart.com/api/v2/accounts/123"
    print("✓ URL construction works correctly\n")
    
    # Test session headers
    print("Testing session headers...")
    session = adapter.session
    assert session.headers['Authorization'] == "Bearer test_token_123"
    assert session.headers['Content-Type'] == "application/json"
    assert 'TesoteOdooConnector' in session.headers['User-Agent']
    print("✓ Session headers are correct\n")
    
    return True


@responses.activate
def test_api_calls():
    """Test API calls with mocked responses."""
    print("\n=== Testing API Calls with Mocked Responses ===\n")
    
    adapter = TesoteAdapterStandalone(
        api_url="https://test-1.miamibeachstart.com",
        api_token="test_token_123"
    )
    
    # Mock status endpoint
    print("Testing status endpoint...")
    responses.add(
        responses.GET,
        "https://test-1.miamibeachstart.com/api/v2/status",
        json={"status": "ok"},
        status=200
    )
    
    result = adapter.get_status()
    assert result["status"] == "ok"
    print("✓ Status endpoint works\n")
    
    # Mock whoami endpoint
    print("Testing whoami endpoint...")
    responses.add(
        responses.GET,
        "https://test-1.miamibeachstart.com/api/v2/whoami",
        json={"name": "Test Client", "environment": "Production"},
        status=200
    )
    
    result = adapter.get_whoami()
    assert result["name"] == "Test Client"
    assert result["environment"] == "Production"
    print("✓ Whoami endpoint works\n")
    
    # Mock sync endpoint
    print("Testing sync endpoint...")
    responses.add(
        responses.POST,
        "https://test-1.miamibeachstart.com/api/v2/transactions/sync",
        json={
            "added": [{"transaction_id": "txn-001", "amount": 100}],
            "modified": [],
            "removed": [],
            "next_cursor": "cursor-123",
            "has_more": False
        },
        status=200
    )
    
    result = adapter.sync_transactions("acc-001", cursor=None, count=100)
    assert len(result["added"]) == 1
    assert result["next_cursor"] == "cursor-123"
    print("✓ Sync endpoint works\n")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESOTE API ADAPTER - STANDALONE TESTS")
    print("=" * 60)
    
    try:
        # Run basic tests
        if test_adapter_basic():
            print("✓ Basic tests passed")
        
        # Run API call tests
        if test_api_calls():
            print("✓ API call tests passed")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())