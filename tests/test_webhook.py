"""
Tests for webhook functionality.
"""
import json
import hmac
import hashlib
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import responses


class TestWebhookConfig(unittest.TestCase):
    """Test webhook configuration model."""

    def setUp(self):
        """Set up test fixtures."""
        self.env = MagicMock()
        self.backend = MagicMock()
        self.backend.id = 1
        self.backend.name = 'Test Backend'

    def test_generate_secret_key(self):
        """Test secret key generation."""
        from models.tesote_webhook_config import TesoteWebhookConfig
        
        config = TesoteWebhookConfig()
        config.env = self.env
        
        secret = config.generate_secret_key()
        
        # Should generate a URL-safe base64 string
        self.assertIsInstance(secret, str)
        self.assertGreater(len(secret), 20)
        # Should be URL-safe (no +, /, or = characters)
        self.assertNotIn('+', secret)
        self.assertNotIn('/', secret)

    def test_verify_signature_valid(self):
        """Test valid webhook signature verification."""
        from models.tesote_webhook_config import TesoteWebhookConfig
        
        config = TesoteWebhookConfig()
        config.env = self.env
        config.ensure_one = MagicMock()
        config.secret_key = 'test_secret_key'
        config.failed_signature_count = 0
        config.backend_id = self.backend
        
        # Create test payload and signature
        payload = '{"event": "test"}'
        timestamp = '1234567890'
        signed_payload = f"{timestamp}.{payload}"
        expected_signature = hmac.new(
            b'test_secret_key',
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        result = config.verify_signature(payload, timestamp, expected_signature)
        
        self.assertTrue(result)
        self.assertEqual(config.failed_signature_count, 0)

    def test_verify_signature_invalid(self):
        """Test invalid webhook signature verification."""
        from models.tesote_webhook_config import TesoteWebhookConfig
        
        config = TesoteWebhookConfig()
        config.env = self.env
        config.ensure_one = MagicMock()
        config.secret_key = 'test_secret_key'
        config.failed_signature_count = 0
        config.backend_id = self.backend
        
        # Create test payload with wrong signature
        payload = '{"event": "test"}'
        timestamp = '1234567890'
        wrong_signature = 'invalid_signature'
        
        # Verify signature
        result = config.verify_signature(payload, timestamp, wrong_signature)
        
        self.assertFalse(result)
        self.assertEqual(config.failed_signature_count, 1)

    def test_get_active_events(self):
        """Test getting list of active webhook events."""
        from models.tesote_webhook_config import TesoteWebhookConfig
        
        config = TesoteWebhookConfig()
        config.env = self.env
        config.ensure_one = MagicMock()
        
        # Set some events as active
        config.subscribe_sync_updates = True
        config.subscribe_account_created = True
        config.subscribe_account_updated = False
        config.subscribe_transaction_created = False
        config.subscribe_transaction_updated = True
        
        events = config.get_active_events()
        
        self.assertIn('sync.updates_available', events)
        self.assertIn('accounts.created', events)
        self.assertNotIn('accounts.updated', events)
        self.assertNotIn('transactions.created', events)
        self.assertIn('transactions.updated', events)


class TestWebhookEvent(unittest.TestCase):
    """Test webhook event model."""

    def setUp(self):
        """Set up test fixtures."""
        self.env = MagicMock()
        self.backend = MagicMock()
        self.backend.id = 1

    def test_check_idempotency_no_duplicate(self):
        """Test idempotency check with no duplicate."""
        from models.tesote_webhook_event import TesoteWebhookEvent
        
        event = TesoteWebhookEvent()
        event.env = self.env
        # Mock search to return empty result (no duplicate)
        event.search = MagicMock(return_value=[])
        
        result = event.check_idempotency('event_123')
        
        self.assertFalse(result)
        event.search.assert_called_once_with([
            ('event_id', '=', 'event_123'),
            ('status', 'in', ['completed', 'processing'])
        ], limit=1)

    def test_check_idempotency_with_duplicate(self):
        """Test idempotency check with duplicate event."""
        from models.tesote_webhook_event import TesoteWebhookEvent
        
        event = TesoteWebhookEvent()
        event.env = self.env
        existing_event = MagicMock()
        event.search = MagicMock(return_value=existing_event)
        
        result = event.check_idempotency('event_123')
        
        self.assertTrue(result)

    def test_get_payload_data_valid_json(self):
        """Test parsing valid JSON payload."""
        from models.tesote_webhook_event import TesoteWebhookEvent
        
        event = TesoteWebhookEvent()
        event.env = self.env
        event.ensure_one = MagicMock()
        event.payload = '{"test": "data", "value": 123}'
        
        result = event.get_payload_data()
        
        self.assertEqual(result, {"test": "data", "value": 123})

    def test_get_payload_data_invalid_json(self):
        """Test parsing invalid JSON payload."""
        from models.tesote_webhook_event import TesoteWebhookEvent
        
        event = TesoteWebhookEvent()
        event.env = self.env
        event.ensure_one = MagicMock()
        event.payload = 'invalid json'
        
        result = event.get_payload_data()
        
        self.assertEqual(result, {})

    def test_log_processing_complete(self):
        """Test logging successful processing."""
        from models.tesote_webhook_event import TesoteWebhookEvent
        
        event = TesoteWebhookEvent()
        event.env = self.env
        event.ensure_one = MagicMock()
        event.event_id = 'test_event'
        event.processing_started_at = datetime(2024, 1, 1, 10, 0, 0)
        
        # Mock fields.Datetime.now()
        with patch('models.tesote_webhook_event.fields.Datetime.now',
                   return_value=datetime(2024, 1, 1, 10, 0, 1)):
            event.log_processing_complete()
        
        self.assertEqual(event.status, 'completed')
        self.assertEqual(event.processing_duration, 1000.0)  # 1 second = 1000ms

    def test_process_sync_updates_available(self):
        """Test processing sync.updates_available webhook."""
        from models.tesote_webhook_event import TesoteWebhookEvent
        
        event = TesoteWebhookEvent()
        event.env = self.env
        event.backend_id = self.backend
        event.event_id = 'test_event'
        
        # Mock account search
        mock_account = MagicMock()
        mock_account.id = 10
        mock_account.name = 'Test Account'
        mock_account.sync_transactions = MagicMock()
        # Make sure hasattr returns False for with_delay so it uses direct sync
        mock_account.with_delay = None
        del mock_account.with_delay
        
        self.env.__getitem__.return_value.sudo.return_value.search.return_value = mock_account
        
        # Test payload
        payload_data = {
            'data': {
                'id': 'acc_123',
                'new_transactions': 5,
                'modified_transactions': 2,
                'removed_transactions': 1
            }
        }
        
        event._process_sync_updates_available(payload_data)
        
        # Should have searched for the account
        self.env.__getitem__.assert_called_with('tesote.account')
        
        # Should have triggered sync
        mock_account.sync_transactions.assert_called_once()

    def test_process_account_created(self):
        """Test processing accounts.created webhook."""
        from models.tesote_webhook_event import TesoteWebhookEvent
        
        event = TesoteWebhookEvent()
        event.env = self.env
        event.backend_id = self.backend
        
        # Mock account model
        mock_account_model = MagicMock()
        mock_account_model.search.return_value = []  # No existing account (empty list)
        mock_account_model.create = MagicMock()
        self.env.__getitem__.return_value.sudo.return_value = mock_account_model
        
        # Test payload
        payload_data = {
            'data': {
                'id': 'acc_new',
                'name': 'New Account',
                'type': 'savings',
                'balance': 1000.0,
                'currency': 'EUR',
                'institution_name': 'Test Bank',
                'active': True
            }
        }
        
        event._process_account_created(payload_data)
        
        # Should have created new account
        mock_account_model.create.assert_called_once()
        call_args = mock_account_model.create.call_args[0][0]
        self.assertEqual(call_args['external_id'], 'acc_new')
        self.assertEqual(call_args['name'], 'New Account')
        self.assertEqual(call_args['account_type'], 'savings')


class TestWebhookController(unittest.TestCase):
    """Test webhook controller."""

    def setUp(self):
        """Set up test fixtures."""
        self.request = MagicMock()
        self.env = MagicMock()
        self.request.env = self.env
        
        # Mock webhook config
        self.webhook_config = MagicMock()
        self.webhook_config.enabled = True
        self.webhook_config.verify_signature = MagicMock(return_value=True)
        self.webhook_config.get_active_events = MagicMock(return_value=['sync.updates_available'])
        self.webhook_config.update_webhook_stats = MagicMock()
        
        self.env.__getitem__.return_value.sudo.return_value.search.return_value = self.webhook_config

    @patch('controllers.webhook_controller.request')
    def test_webhook_endpoint_success(self, mock_request):
        """Test successful webhook processing."""
        from controllers.webhook_controller import TesoteWebhookController
        
        # Mock the singleton backend
        mock_backend = MagicMock()
        mock_backend.id = 1
        
        mock_request.env = self.env
        mock_request.httprequest = MagicMock()
        
        # Mock request headers
        mock_request.httprequest.headers = {
            'X-Tesote-Webhook-Id': 'webhook_123',
            'X-Tesote-Event-Type': 'sync.updates_available',
            'X-Tesote-Signature': 'valid_signature',
            'X-Tesote-Timestamp': '1234567890'
        }
        mock_request.httprequest.data = b'{"data": {"id": "acc_123"}}'
        mock_request.httprequest.remote_addr = '192.168.1.1'
        
        # Mock webhook event model
        mock_event = MagicMock()
        mock_event.log_webhook_receipt = MagicMock()
        mock_event_model = MagicMock()
        mock_event_model.check_idempotency = MagicMock(return_value=False)
        mock_event_model.create = MagicMock(return_value=mock_event)
        
        # Setup env mocking to handle different model requests
        def env_getitem(key):
            mock_obj = MagicMock()
            if key == 'tesote.backend':
                mock_obj.sudo.return_value.search.return_value = mock_backend
            elif key == 'tesote.webhook.config':
                mock_obj.sudo.return_value.search.return_value = self.webhook_config
            elif key == 'tesote.webhook.event':
                mock_obj.sudo.return_value = mock_event_model
            return mock_obj
        
        mock_request.env.__getitem__.side_effect = env_getitem
        
        controller = TesoteWebhookController()
        result = controller.webhook_endpoint()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['event_id'], 'webhook_123')
        
        # Should have created webhook event
        mock_event_model.create.assert_called_once()
        
        # Should have updated webhook stats
        self.webhook_config.update_webhook_stats.assert_called_once()

    @patch('controllers.webhook_controller.request')
    def test_webhook_endpoint_invalid_signature(self, mock_request):
        """Test webhook with invalid signature."""
        from controllers.webhook_controller import TesoteWebhookController
        
        # Mock the singleton backend
        mock_backend = MagicMock()
        mock_backend.id = 1
        
        mock_request.env = self.env
        mock_request.httprequest = MagicMock()
        
        # Mock request headers
        mock_request.httprequest.headers = {
            'X-Tesote-Webhook-Id': 'webhook_123',
            'X-Tesote-Event-Type': 'sync.updates_available',
            'X-Tesote-Signature': 'invalid_signature',
            'X-Tesote-Timestamp': '1234567890'
        }
        mock_request.httprequest.data = b'{"data": {"id": "acc_123"}}'
        
        # Mock invalid signature verification
        self.webhook_config.verify_signature = MagicMock(return_value=False)
        
        # Setup env mocking
        def env_getitem(key):
            mock_obj = MagicMock()
            if key == 'tesote.backend':
                mock_obj.sudo.return_value.search.return_value = mock_backend
            elif key == 'tesote.webhook.config':
                mock_obj.sudo.return_value.search.return_value = self.webhook_config
            return mock_obj
        
        mock_request.env.__getitem__.side_effect = env_getitem
        
        controller = TesoteWebhookController()
        result = controller.webhook_endpoint()
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Invalid signature')

    @patch('controllers.webhook_controller.request')
    def test_webhook_endpoint_idempotency(self, mock_request):
        """Test webhook idempotency handling."""
        from controllers.webhook_controller import TesoteWebhookController
        
        # Mock the singleton backend
        mock_backend = MagicMock()
        mock_backend.id = 1
        
        mock_request.env = self.env
        mock_request.httprequest = MagicMock()
        
        # Mock request headers
        mock_request.httprequest.headers = {
            'X-Tesote-Webhook-Id': 'webhook_duplicate',
            'X-Tesote-Event-Type': 'sync.updates_available',
            'X-Tesote-Signature': 'valid_signature',
            'X-Tesote-Timestamp': '1234567890'
        }
        mock_request.httprequest.data = b'{"data": {"id": "acc_123"}}'
        
        # Mock duplicate event (idempotency check returns True)
        mock_event_model = MagicMock()
        mock_event_model.check_idempotency = MagicMock(return_value=True)
        
        # Setup env mocking
        def env_getitem(key):
            mock_obj = MagicMock()
            if key == 'tesote.backend':
                mock_obj.sudo.return_value.search.return_value = mock_backend
            elif key == 'tesote.webhook.config':
                mock_obj.sudo.return_value.search.return_value = self.webhook_config
            elif key == 'tesote.webhook.event':
                mock_obj.sudo.return_value = mock_event_model
            return mock_obj
        
        mock_request.env.__getitem__.side_effect = env_getitem
        
        controller = TesoteWebhookController()
        result = controller.webhook_endpoint()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message'], 'Already processed')


if __name__ == '__main__':
    unittest.main()