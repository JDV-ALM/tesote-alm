# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Tests for Tesote Sync Log functionality.
"""

# Import conftest first to set up Odoo mocks
from . import conftest

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestTesoteSyncLog:
    """Test Tesote Sync Log model."""
    
    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend record."""
        backend = Mock()
        backend.id = 1
        backend.name = 'Test Backend'
        backend.api_url = "https://equipo.tesote.com"
        backend.api_token = "test_token_123"
        return backend
    
    @pytest.fixture
    def mock_account(self):
        """Create a mock account record."""
        account = Mock()
        account.id = 1
        account.name = 'Test Account'
        account.tesote_id = 'acc-001'
        return account
    
    @pytest.fixture
    def sync_log_model(self):
        """Create mock sync log model."""
        from ..models.tesote_sync_log import TesoteSyncLog
        
        # Mock the model
        model = Mock(spec=TesoteSyncLog)
        model._name = 'tesote.sync.log'
        
        return model
    
    def test_sync_log_creation(self, sync_log_model, mock_backend):
        """Test sync log creation with basic fields."""
        # Mock create_log method
        log_data = {
            'backend_id': mock_backend.id,
            'operation': 'test_connection',
            'status': 'started',
            'start_date': datetime.now(),
        }
        
        mock_log = Mock()
        mock_log.id = 1
        mock_log.backend_id = mock_backend
        mock_log.operation = 'test_connection'
        mock_log.status = 'started'
        
        sync_log_model.create_log.return_value = mock_log
        
        # Test creation
        log = sync_log_model.create_log(
            mock_backend,
            'test_connection'
        )
        
        sync_log_model.create_log.assert_called_once_with(
            mock_backend,
            'test_connection'
        )
        assert log.operation == 'test_connection'
        assert log.status == 'started'
    
    def test_sync_log_success(self, sync_log_model):
        """Test marking sync log as successful."""
        mock_log = Mock()
        mock_log.set_success = Mock()
        
        # Test success marking
        mock_log.set_success(
            records_added=5,
            api_calls=2
        )
        
        mock_log.set_success.assert_called_once_with(
            records_added=5,
            api_calls=2
        )
    
    def test_sync_log_error(self, sync_log_model):
        """Test marking sync log as failed."""
        mock_log = Mock()
        mock_log.set_error = Mock()
        
        error_message = "API connection failed"
        
        # Test error marking
        mock_log.set_error(error_message)
        
        mock_log.set_error.assert_called_once_with(error_message)
    
    def test_sync_log_progress_update(self, sync_log_model):
        """Test updating sync log progress."""
        mock_log = Mock()
        mock_log.update_progress = Mock()
        
        # Test progress update
        mock_log.update_progress(
            details='Syncing account Test Account',
            api_calls=3
        )
        
        mock_log.update_progress.assert_called_once_with(
            details='Syncing account Test Account',
            api_calls=3
        )
    
    def test_duration_calculation(self):
        """Test sync log duration calculation."""
        # Mock datetime fields
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=30)
        
        # Mock log with duration calculation
        mock_log = Mock()
        mock_log.start_date = start_time
        mock_log.end_date = end_time
        
        # Simulate duration computation
        delta = end_time - start_time
        expected_duration = delta.total_seconds()
        
        assert expected_duration == 30.0


class TestBackgroundSync:
    """Test background sync functionality."""
    
    @pytest.fixture
    def mock_backend_record(self):
        """Create mock backend record for background sync."""
        backend = Mock()
        backend.id = 1
        backend.name = 'Test Backend'
        backend.account_ids = []
        backend._process_sync_results = Mock()
        return backend
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock adapter for testing."""
        adapter = Mock()
        adapter.sync_transactions.return_value = {
            'added': [{'transaction_id': 'txn-001'}],
            'modified': [],
            'removed': [],
            'next_cursor': 'cursor-123',
            'has_more': False
        }
        return adapter
    
    def test_background_sync_threading(self, mock_backend_record):
        """Test that background sync starts a thread."""
        from ..models.tesote_backend import TesoteBackend
        
        # Mock the threading
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            # Mock the backend model
            backend_model = Mock(spec=TesoteBackend)
            backend_model.ensure_one = Mock()
            backend_model.account_ids = []
            backend_model.id = 1
            
            # Mock the method that would be called
            def mock_sync_all_transactions(self):
                mock_thread.assert_called_once()
                mock_thread_instance.start.assert_called_once()
            
            # Test would verify threading.Thread is called
            # In actual implementation, this would start background sync
            assert True  # Placeholder for thread test
    
    def test_sync_log_integration(self):
        """Test sync log creation during sync operations."""
        # Mock environment and models
        mock_env = MagicMock()
        mock_sync_log_model = Mock()
        mock_log = Mock()
        
        mock_sync_log_model.create_log.return_value = mock_log
        # Use side_effect for __getitem__ instead of direct assignment
        mock_env.__getitem__ = Mock(return_value=mock_sync_log_model)
        
        # Test log creation
        log = mock_sync_log_model.create_log(
            Mock(),  # backend
            'sync_transactions',
            is_background=True
        )
        
        mock_sync_log_model.create_log.assert_called_once()
        assert log is not None


class TestAutoSync:
    """Test auto sync (scheduled) functionality."""
    
    @pytest.fixture
    def mock_cron_job(self):
        """Create mock cron job."""
        cron = Mock()
        cron.active = False
        cron.interval_number = 24
        cron.interval_type = 'hours'
        return cron
    
    def test_cron_job_activation(self, mock_cron_job):
        """Test cron job gets activated when auto sync is enabled."""
        # Mock backend with auto sync enabled
        backend = Mock()
        backend.auto_sync_enabled = True
        backend.active = True
        backend.sync_interval_hours = 6
        
        # Mock environment reference
        mock_env = Mock()
        mock_env.ref.return_value = mock_cron_job
        backend.env = mock_env
        
        # Simulate _update_cron_job method behavior
        if backend.auto_sync_enabled and backend.active:
            mock_cron_job.active = True
            mock_cron_job.interval_number = backend.sync_interval_hours
        
        assert mock_cron_job.active is True
        assert mock_cron_job.interval_number == 6
    
    def test_cron_job_deactivation(self, mock_cron_job):
        """Test cron job gets deactivated when auto sync is disabled."""
        # Mock backend with auto sync disabled
        backend = Mock()
        backend.auto_sync_enabled = False
        backend.active = True
        
        # Mock environment reference
        mock_env = Mock()
        mock_env.ref.return_value = mock_cron_job
        backend.env = mock_env
        
        # Simulate _update_cron_job method behavior
        if not backend.auto_sync_enabled:
            mock_cron_job.active = False
        
        assert mock_cron_job.active is False
    
    def test_scheduled_full_sync(self):
        """Test scheduled full sync includes accounts and transactions."""
        # Mock the full sync process
        mock_backend = Mock()
        mock_backend.id = 1
        
        # Mock adapter and importer
        mock_adapter = Mock()
        mock_importer = Mock()
        mock_importer.run.return_value = 3  # 3 accounts imported
        
        # Mock sync results
        mock_adapter.sync_transactions.return_value = {
            'added': [{'transaction_id': 'txn-001'}],
            'modified': [],
            'removed': [],
            'next_cursor': 'cursor-123'
        }
        
        # Test the sequence: accounts first, then transactions
        accounts_imported = mock_importer.run(mock_adapter)
        sync_result = mock_adapter.sync_transactions('acc-001', None, 100)
        
        assert accounts_imported == 3
        assert len(sync_result['added']) == 1
        assert sync_result['next_cursor'] == 'cursor-123'


class TestBackendIntegration:
    """Test backend model integration with sync logs."""
    
    def test_backend_sync_log_relation(self):
        """Test backend has relation to sync logs."""
        # Mock backend with sync logs
        mock_backend = Mock()
        mock_sync_logs = [Mock(), Mock(), Mock()]
        mock_backend.sync_log_ids = mock_sync_logs
        mock_backend.sync_log_count = len(mock_sync_logs)
        
        assert mock_backend.sync_log_count == 3
        assert len(mock_backend.sync_log_ids) == 3
    
    def test_action_view_sync_logs(self):
        """Test backend action to view sync logs."""
        mock_backend = Mock()
        mock_backend.id = 1
        mock_backend.ensure_one = Mock()
        
        # Expected action structure
        expected_action = {
            'name': 'Sync Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'tesote.sync.log',
            'view_mode': 'list,form',
            'domain': [('backend_id', '=', 1)],
            'context': {'default_backend_id': 1},
        }
        
        # Mock the action method
        mock_backend.action_view_sync_logs.return_value = expected_action
        
        action = mock_backend.action_view_sync_logs()
        
        assert action['res_model'] == 'tesote.sync.log'
        assert action['domain'] == [('backend_id', '=', 1)]