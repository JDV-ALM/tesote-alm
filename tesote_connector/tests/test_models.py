# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Test Tesote models following TDD principles.
"""

from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime


class TestTesoteBackend:
    """Test Tesote Backend model."""
    
    @pytest.fixture
    def mock_env(self):
        """Create mock Odoo environment."""
        env = Mock()
        env.user = Mock()
        env.user.company_id = Mock(id=1)
        return env
    
    def test_backend_model_fields(self):
        """Test that backend model has required fields."""
        from ..models.tesote_backend import TesoteBackend
        
        # Check required fields exist
        assert hasattr(TesoteBackend, 'name')
        assert hasattr(TesoteBackend, 'api_url')
        assert hasattr(TesoteBackend, 'api_version')
        assert hasattr(TesoteBackend, 'api_token')
        assert hasattr(TesoteBackend, 'rate_limit_calls')
        assert hasattr(TesoteBackend, 'rate_limit_period')
        assert hasattr(TesoteBackend, 'active')
    
    def test_backend_defaults(self, mock_env):
        """Test backend model default values."""
        from ..models.tesote_backend import TesoteBackend
        
        backend = TesoteBackend(mock_env)
        
        # Test defaults
        assert backend._defaults.get('api_version') == 'v1'
        assert backend._defaults.get('api_url') == 'https://staging.tesote.com'
        assert backend._defaults.get('rate_limit_calls') == 100
        assert backend._defaults.get('rate_limit_period') == 60
        assert backend._defaults.get('active') is True
    
    def test_backend_test_connection(self, mock_env):
        """Test backend connection testing method."""
        from ..models.tesote_backend import TesoteBackend
        
        backend = TesoteBackend(mock_env)
        backend.api_token = 'test_token'
        
        with patch('odoo.addons.tesote_connector.models.tesote_backend.TesoteAdapter') as MockAdapter:
            mock_adapter = Mock()
            mock_adapter.check_status.return_value = {
                'status': 'ok',
                'authenticated': True
            }
            MockAdapter.return_value = mock_adapter
            
            # Test successful connection
            result = backend.test_connection()
            assert result is True
    
    def test_import_accounts_action(self, mock_env):
        """Test action to import accounts."""
        from ..models.tesote_backend import TesoteBackend
        
        backend = TesoteBackend(mock_env)
        backend.id = 1
        
        # Test import accounts action
        action = backend.import_accounts()
        
        assert action['type'] == 'ir.actions.act_window'
        assert action['res_model'] == 'tesote.import.accounts.wizard'
        assert action['context']['default_backend_id'] == 1


class TestTesoteAccount:
    """Test Tesote Account model."""
    
    @pytest.fixture
    def mock_env(self):
        """Create mock Odoo environment."""
        env = Mock()
        env['res.partner'] = Mock()
        env['tesote.backend'] = Mock()
        return env
    
    def test_account_model_fields(self):
        """Test that account model has required fields."""
        from ..models.tesote_account import TesoteAccount
        
        # Check required fields
        assert hasattr(TesoteAccount, 'name')
        assert hasattr(TesoteAccount, 'tesote_id')
        assert hasattr(TesoteAccount, 'backend_id')
        assert hasattr(TesoteAccount, 'partner_id')
        assert hasattr(TesoteAccount, 'bank_name')
        assert hasattr(TesoteAccount, 'legal_entity_name')
        assert hasattr(TesoteAccount, 'tesote_created_at')
        assert hasattr(TesoteAccount, 'tesote_updated_at')
        assert hasattr(TesoteAccount, 'active')
    
    def test_account_unique_constraint(self):
        """Test unique constraint on tesote_id per backend."""
        from ..models.tesote_account import TesoteAccount
        
        # Check SQL constraints
        constraints = TesoteAccount._sql_constraints
        
        # Should have unique constraint on tesote_id + backend_id
        unique_constraint = [c for c in constraints if 'unique' in c[2].lower()]
        assert len(unique_constraint) > 0
    
    def test_account_sync_method(self, mock_env):
        """Test account synchronization method."""
        from ..models.tesote_account import TesoteAccount
        
        account = TesoteAccount(mock_env)
        account.tesote_id = 'acc-001'
        account.backend_id = Mock(id=1)
        
        with patch('odoo.addons.tesote_connector.models.tesote_account.AccountImporter') as MockImporter:
            mock_importer = Mock()
            MockImporter.return_value = mock_importer
            
            # Test sync
            account.sync_from_tesote()
            
            # Verify importer was called
            mock_importer.run.assert_called_once()


class TestTesoteTransaction:
    """Test Tesote Transaction model."""
    
    @pytest.fixture
    def mock_env(self):
        """Create mock Odoo environment."""
        env = Mock()
        env['tesote.account'] = Mock()
        env['account.move'] = Mock()
        return env
    
    def test_transaction_model_fields(self):
        """Test that transaction model has required fields."""
        from ..models.tesote_transaction import TesoteTransaction
        
        # Check required fields
        assert hasattr(TesoteTransaction, 'name')
        assert hasattr(TesoteTransaction, 'tesote_id')
        assert hasattr(TesoteTransaction, 'account_id')
        assert hasattr(TesoteTransaction, 'amount')
        assert hasattr(TesoteTransaction, 'currency_id')
        assert hasattr(TesoteTransaction, 'transaction_date')
        assert hasattr(TesoteTransaction, 'status')
        assert hasattr(TesoteTransaction, 'description')
        assert hasattr(TesoteTransaction, 'counterparty_name')
        assert hasattr(TesoteTransaction, 'categories')
        assert hasattr(TesoteTransaction, 'tesote_imported_at')
        assert hasattr(TesoteTransaction, 'tesote_updated_at')
        assert hasattr(TesoteTransaction, 'account_move_id')
    
    def test_transaction_status_selection(self):
        """Test transaction status field selection values."""
        from ..models.tesote_transaction import TesoteTransaction
        
        # Get status field
        status_field = TesoteTransaction._fields.get('status')
        
        # Check selection values
        expected_statuses = [
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled')
        ]
        
        for status in expected_statuses:
            assert status in status_field.selection
    
    def test_transaction_to_journal_entry(self, mock_env):
        """Test converting transaction to journal entry."""
        from ..models.tesote_transaction import TesoteTransaction
        
        transaction = TesoteTransaction(mock_env)
        transaction.amount = 100.00
        transaction.description = "Test transaction"
        transaction.account_id = Mock(partner_id=Mock(id=1))
        
        # Test journal entry creation
        with patch.object(transaction, '_create_journal_entry') as mock_create:
            mock_create.return_value = Mock(id=1)
            
            entry = transaction.create_journal_entry()
            
            assert entry.id == 1
            mock_create.assert_called_once()
    
    def test_transaction_unique_constraint(self):
        """Test unique constraint on transaction."""
        from ..models.tesote_transaction import TesoteTransaction
        
        # Check SQL constraints
        constraints = TesoteTransaction._sql_constraints
        
        # Should have unique constraint on tesote_id + account_id
        unique_constraint = [c for c in constraints if 'unique' in c[2].lower()]
        assert len(unique_constraint) > 0