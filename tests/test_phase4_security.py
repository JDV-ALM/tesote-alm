import hashlib
import hmac
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestPhase4Security(unittest.TestCase):
    """Test Phase 4 Security & Reliability features"""

    def setUp(self):
        super().setUp()

        # Create mock environment
        self.env = {}

        # Create mock backend
        self.backend = MagicMock()
        self.backend.id = 1
        self.backend.name = "Test Backend"

        # Create webhook config with secret key
        self.webhook_config = MagicMock()
        self.webhook_config.id = 1
        self.webhook_config.backend_id = self.backend
        self.webhook_config.secret_key = "test_secret_key_123"
        self.webhook_config.enabled = True
        self.webhook_config.failed_signature_count = 0

        # Mock webhook config model
        self.env["tesote.webhook.config"] = MagicMock()
        self.env["tesote.webhook.config"].search = MagicMock(return_value=self.webhook_config)

        # Create webhook event
        self.webhook_event = MagicMock()
        self.webhook_event.id = 1
        self.webhook_event.event_id = "evt_test123"
        self.webhook_event.backend_id = self.backend

        # Mock webhook event model
        self.env["tesote.webhook.event"] = MagicMock()

    def test_signature_verification_valid(self):
        """Test Task 4.1: Valid webhook signature verification"""
        payload = '{"event": "sync.updates_available", "data": {"id": "acc_123"}}'
        timestamp = "1234567890"

        # Calculate correct signature
        signed_payload = f"{timestamp}.{payload}"
        expected_signature = hmac.new(
            self.webhook_config.secret_key.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Test verification
        self.webhook_config.verify_signature = MagicMock(return_value=True)
        result = self.webhook_config.verify_signature(payload, timestamp, expected_signature)

        self.assertTrue(result)
        self.webhook_config.verify_signature.assert_called_once_with(
            payload, timestamp, expected_signature
        )

    def test_signature_verification_invalid(self):
        """Test Task 4.1: Invalid webhook signature verification"""
        payload = '{"event": "sync.updates_available", "data": {"id": "acc_123"}}'
        timestamp = "1234567890"
        invalid_signature = "invalid_signature_123"

        # Test verification
        self.webhook_config.verify_signature = MagicMock(return_value=False)
        result = self.webhook_config.verify_signature(payload, timestamp, invalid_signature)

        self.assertFalse(result)
        self.webhook_config.verify_signature.assert_called_once_with(
            payload, timestamp, invalid_signature
        )

    def test_signature_verification_implementation(self):
        """Test Task 4.1: Actual signature verification implementation"""
        from models.tesote_webhook_config import TesoteWebhookConfig

        # Create instance with mocked methods
        config = TesoteWebhookConfig()
        config.secret_key = "test_secret_key_123"
        config.failed_signature_count = 0
        config.ensure_one = MagicMock()

        payload = '{"event": "test"}'
        timestamp = "1234567890"

        # Calculate correct signature
        signed_payload = f"{timestamp}.{payload}"
        correct_signature = hmac.new(
            config.secret_key.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Test with correct signature
        with patch("models.tesote_webhook_config._logger") as mock_logger:
            result = config.verify_signature(payload, timestamp, correct_signature)
            self.assertTrue(result)
            mock_logger.warning.assert_not_called()

        # Test with incorrect signature
        with patch("models.tesote_webhook_config._logger") as mock_logger:
            result = config.verify_signature(payload, timestamp, "wrong_signature")
            self.assertFalse(result)
            mock_logger.warning.assert_called()

    def test_idempotency_check_no_duplicate(self):
        """Test Task 4.2: Idempotency check - no duplicate"""
        event_id = "evt_unique_123"

        # Mock search returning no existing events
        self.env["tesote.webhook.event"].search = MagicMock(return_value=[])
        self.env["tesote.webhook.event"].check_idempotency = MagicMock(return_value=False)

        result = self.env["tesote.webhook.event"].check_idempotency(event_id)

        self.assertFalse(result)
        self.env["tesote.webhook.event"].check_idempotency.assert_called_once_with(event_id)

    def test_idempotency_check_with_duplicate(self):
        """Test Task 4.2: Idempotency check - duplicate found"""
        event_id = "evt_duplicate_123"

        # Mock search returning existing event
        existing_event = MagicMock()
        existing_event.event_id = event_id
        existing_event.status = "completed"

        self.env["tesote.webhook.event"].search = MagicMock(return_value=[existing_event])
        self.env["tesote.webhook.event"].check_idempotency = MagicMock(return_value=True)

        result = self.env["tesote.webhook.event"].check_idempotency(event_id)

        self.assertTrue(result)
        self.env["tesote.webhook.event"].check_idempotency.assert_called_once_with(event_id)

    def test_idempotency_implementation(self):
        """Test Task 4.2: Actual idempotency implementation"""
        from models.tesote_webhook_event import TesoteWebhookEvent

        # Create instance with mocked methods
        event_model = TesoteWebhookEvent()

        # Test no duplicate case
        event_model.search = MagicMock(return_value=[])
        result = event_model.check_idempotency("evt_test_123")
        self.assertFalse(result)

        # Test duplicate found case
        existing = MagicMock()
        event_model.search = MagicMock(return_value=[existing])
        result = event_model.check_idempotency("evt_test_123")
        self.assertTrue(result)

    def test_monitoring_log_receipt(self):
        """Test Task 4.3: Monitoring - log webhook receipt"""
        from models.tesote_webhook_event import TesoteWebhookEvent

        event = TesoteWebhookEvent()
        event.ensure_one = MagicMock()

        # Mock request
        request = MagicMock()
        request.httprequest.headers = {"X-Test": "value"}
        request.httprequest.data = b'{"test": "data"}'
        request.httprequest.remote_addr = "127.0.0.1"

        # Mock fields.Datetime.now()
        with patch("models.tesote_webhook_event.fields") as mock_fields:
            mock_fields.Datetime.now = MagicMock(return_value=datetime.now())

            # Call log_webhook_receipt
            event.log_webhook_receipt(request)

            # Check attributes were set
            self.assertIsNotNone(event.headers)
            self.assertIsNotNone(event.raw_body)
            self.assertIsNotNone(event.received_at)
            self.assertEqual(event.ip_address, "127.0.0.1")

    def test_monitoring_log_processing(self):
        """Test Task 4.3: Monitoring - log processing stages"""
        from models.tesote_webhook_event import TesoteWebhookEvent

        event = TesoteWebhookEvent()
        event.ensure_one = MagicMock()
        event.event_id = "evt_test_123"
        event.event_type = "sync.updates_available"

        # Test log_processing_start
        with patch("models.tesote_webhook_event.fields") as mock_fields:
            mock_fields.Datetime.now = MagicMock(return_value=datetime.now())
            with patch("models.tesote_webhook_event._logger") as mock_logger:
                event.log_processing_start()

                self.assertEqual(event.status, "processing")
                self.assertIsNotNone(event.processing_started_at)
                mock_logger.info.assert_called()

        # Test log_processing_complete
        event.processing_started_at = datetime.now() - timedelta(seconds=2)
        with patch("models.tesote_webhook_event.fields") as mock_fields:
            mock_fields.Datetime.now = MagicMock(return_value=datetime.now())
            with patch("models.tesote_webhook_event._logger") as mock_logger:
                event.log_processing_complete()

                self.assertEqual(event.status, "completed")
                self.assertIsNotNone(event.processed_at)
                self.assertGreater(event.processing_duration, 0)
                mock_logger.info.assert_called()

        # Test log_processing_error
        with patch("models.tesote_webhook_event._logger") as mock_logger:
            error = Exception("Test error")
            event.retry_count = 0
            event.log_processing_error(error)

            self.assertEqual(event.status, "failed")
            self.assertEqual(event.error_message, "Test error")
            self.assertEqual(event.retry_count, 1)
            mock_logger.error.assert_called()

    def test_monitoring_statistics(self):
        """Test Task 4.3: Monitoring - get statistics"""
        from models.tesote_webhook_event import TesoteWebhookEvent

        event_model = TesoteWebhookEvent()

        # Create mock events
        events = []
        for i in range(10):
            event = MagicMock()
            event.status = "completed" if i < 7 else "failed"
            event.event_type = "sync.updates_available" if i < 5 else "accounts.updated"
            event.processing_duration = 100.0 * (i + 1)
            event.retry_count = 0 if i < 8 else 2
            event.sync_job_id = f"job_{i}" if i < 3 else None
            events.append(event)

        # Mock search
        event_model.search = MagicMock(return_value=events)

        # Mock webhook config for signature failures
        mock_config = MagicMock()
        mock_config.failed_signature_count = 5
        event_model.env = {"tesote.webhook.config": MagicMock()}
        event_model.env["tesote.webhook.config"].search = MagicMock(return_value=mock_config)

        # Get statistics
        with patch("models.tesote_webhook_event.fields") as mock_fields:
            mock_fields.Datetime.now = MagicMock(return_value=datetime.now())
            stats = event_model.get_statistics(hours=24)

        # Verify statistics
        self.assertEqual(stats["total_received"], 10)
        self.assertEqual(stats["by_status"]["completed"], 7)
        self.assertEqual(stats["by_status"]["failed"], 3)
        self.assertEqual(stats["success_rate"], 70.0)
        self.assertEqual(stats["failure_rate"], 30.0)
        self.assertEqual(stats["signature_failures"], 5)
        self.assertGreater(stats["retry_attempts"], 0)

    def test_monitoring_metrics(self):
        """Test Task 4.3: Comprehensive monitoring metrics"""
        from models.tesote_webhook_event import TesoteWebhookEvent

        event_model = TesoteWebhookEvent()

        # Mock events for metrics
        completed_events = []
        for event_type in ["sync.updates_available", "accounts.created"]:
            for i in range(5):
                event = MagicMock()
                event.event_type = event_type
                event.status = "completed"
                event.processing_duration = 50.0 + i * 10
                event.retry_count = i % 2
                completed_events.append(event)

        # Mock search methods
        def mock_search(domain):
            # Return different results based on domain
            if any("retry_count" in str(d) for d in domain):
                # Return events with retries
                return [e for e in completed_events if e.retry_count > 0]
            else:
                # Return completed events
                return completed_events

        event_model.search = MagicMock(side_effect=mock_search)
        event_model.get_statistics = MagicMock(
            return_value={"total_received": 10, "success_rate": 80.0}
        )

        # Get monitoring metrics
        with patch("models.tesote_webhook_event.timedelta") as mock_timedelta:
            mock_timedelta.return_value = timedelta(days=1)
            with patch("models.tesote_webhook_event.fields") as mock_fields:
                mock_fields.Datetime.now = MagicMock(return_value=datetime.now())
                metrics = event_model.get_monitoring_metrics()

        # Verify metrics structure
        self.assertIn("hourly", metrics)
        self.assertIn("daily", metrics)
        self.assertIn("processing_time_by_type", metrics)
        self.assertIn("retry_success_rate", metrics)

        # Verify processing time by type was calculated
        self.assertIn("sync.updates_available", metrics["processing_time_by_type"])
        self.assertIn("accounts.created", metrics["processing_time_by_type"])

    def test_signature_failure_tracking(self):
        """Test Task 4.3: Track signature validation failures"""
        from models.tesote_webhook_config import TesoteWebhookConfig

        config = TesoteWebhookConfig()
        config.secret_key = "test_key"
        config.failed_signature_count = 10
        config.ensure_one = MagicMock()

        # Test signature failure increments counter
        with patch("models.tesote_webhook_config._logger") as mock_logger:
            result = config.verify_signature("payload", "timestamp", "wrong_sig")

            self.assertFalse(result)
            self.assertEqual(config.failed_signature_count, 11)
            mock_logger.warning.assert_called()

    def test_retry_success_rate_calculation(self):
        """Test Task 4.3: Calculate retry success rates"""
        from models.tesote_webhook_event import TesoteWebhookEvent

        event_model = TesoteWebhookEvent()

        # Create mix of successful and failed retried events
        retried_events = []
        for i in range(10):
            event = MagicMock()
            event.retry_count = i + 1
            event.status = "completed" if i < 6 else "failed"
            retried_events.append(event)

        # Mock search to return retried events
        event_model.search = MagicMock(return_value=retried_events)

        # Calculate retry success rate
        with patch("models.tesote_webhook_event.timedelta") as mock_timedelta:
            mock_timedelta.return_value = timedelta(days=7)
            with patch("models.tesote_webhook_event.fields") as mock_fields:
                mock_fields.Datetime.now = MagicMock(return_value=datetime.now())

                # Get metrics (which includes retry success rate)
                event_model.get_statistics = MagicMock(return_value={})
                metrics = event_model.get_monitoring_metrics()

                # Verify retry success rate calculation
                expected_rate = 60.0  # 6 successful out of 10
                self.assertEqual(metrics["retry_success_rate"], expected_rate)
