import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import mocking setup (sets up all Odoo mocks)
import tests.conftest  # noqa: F401


class TestWebhookProcessor(unittest.TestCase):
    """Test webhook processor component."""

    def setUp(self):
        super().setUp()

        # Create mock env
        self.env = Mock()
        self.env.__getitem__ = Mock(side_effect=self._mock_env_getitem)

        # Set up model mocks
        self.webhook_event_model = Mock()
        self.account_model = Mock()
        self.transaction_model = Mock()

        from components.webhook_processor import WebhookProcessor

        self.processor = WebhookProcessor(self.env)

        self.backend = Mock()
        self.backend.id = 1
        self.backend.name = "Test Backend"

        self.webhook_event = Mock()
        self.webhook_event.id = 1
        self.webhook_event.event_id = "evt_123abc"
        self.webhook_event.event_type = "sync.updates_available"
        self.webhook_event.backend_id = self.backend
        self.webhook_event.retry_count = 0
        self.webhook_event.exists.return_value = True

    def _mock_env_getitem(self, model_name):
        """Mock env[] access."""
        mock_model = Mock()
        mock_model.sudo.return_value = mock_model  # Make sudo() return itself

        if model_name == "tesote.webhook.event":
            mock_model.browse = self.webhook_event_model.browse
            mock_model.search = self.webhook_event_model.search
            return mock_model
        elif model_name == "tesote.account":
            mock_model.search = self.account_model.search
            mock_model.create = self.account_model.create
            return mock_model
        elif model_name == "tesote.transaction":
            mock_model.search = self.transaction_model.search
            mock_model.create = self.transaction_model.create
            return mock_model
        return mock_model

    def test_process_event_success(self):
        """Test successful webhook event processing."""
        self.webhook_event.get_payload_data.return_value = {
            "data": {
                "id": "acc_123",
                "new_transactions": 5,
                "modified_transactions": 2,
                "removed_transactions": 1,
            }
        }

        account = Mock()
        account.id = 1
        account.name = "Test Account"

        backend = Mock()
        backend.id = 1
        backend.sync_transactions_v2 = Mock()
        self.webhook_event.backend_id = backend

        # Mock with_delay on backend
        job = Mock()
        job.uuid = "job_uuid_test"
        backend.with_delay = Mock()
        backend.with_delay.return_value.sync_transactions_v2 = Mock(return_value=job)

        self.webhook_event_model.browse.return_value = self.webhook_event
        self.account_model.search.return_value = account

        result = self.processor.process_event(1)

        self.assertTrue(result)
        self.webhook_event.log_processing_start.assert_called_once()
        self.webhook_event.log_processing_complete.assert_called_once()
        # The sync_transactions_v2 is called on backend via with_delay
        backend.with_delay.assert_called()

    def test_process_event_not_found(self):
        """Test processing non-existent webhook event."""
        self.webhook_event.exists.return_value = False

        self.webhook_event_model.browse.return_value = self.webhook_event

        result = self.processor.process_event(999)

        self.assertFalse(result)

    def test_handle_sync_updates_with_delay(self):
        """Test sync.updates_available webhook with queue_job."""
        payload_data = {
            "data": {
                "id": "acc_456",
                "new_transactions": 10,
                "modified_transactions": 5,
                "removed_transactions": 2,
            }
        }

        account = Mock()
        account.id = 2
        account.name = "Account 456"

        backend = Mock()
        backend.id = 1
        job = Mock()
        job.uuid = "job_uuid_123"
        backend.with_delay = Mock()
        backend.with_delay.return_value.sync_transactions_v2 = Mock(return_value=job)
        self.webhook_event.backend_id = backend

        self.account_model.search.return_value = account

        self.processor._handle_sync_updates(self.webhook_event, payload_data)

        backend.with_delay.assert_called_once()
        self.assertEqual(self.webhook_event.sync_job_id, "job_uuid_123")

    def test_handle_sync_updates_account_not_found(self):
        """Test sync.updates_available when account doesn't exist."""
        payload_data = {"data": {"id": "acc_notfound", "new_transactions": 1}}

        self.account_model.search.return_value = None

        with patch.object(self.processor, "_fetch_and_create_account") as mock_fetch:
            mock_fetch.return_value = None

            with self.assertRaises(ValueError) as ctx:
                self.processor._handle_sync_updates(self.webhook_event, payload_data)

            self.assertIn("Could not find or create account", str(ctx.exception))

    def test_handle_account_created(self):
        """Test accounts.created webhook processing."""
        payload_data = {
            "data": {
                "id": "acc_new",
                "name": "New Account",
                "type": "savings",
                "balance": 1000.00,
                "currency": "USD",
                "institution_name": "Test Bank",
                "active": True,
                "sync_required": True,
            }
        }

        new_account = Mock(spec=["id", "name"])  # Use spec to limit attributes
        new_account.id = 3
        new_account.name = "New Account"

        backend = Mock(
            spec=["id", "sync_transactions_v2"]
        )  # Use spec to limit attributes (no with_delay)
        backend.id = 1
        backend.sync_transactions_v2 = Mock()
        self.webhook_event.backend_id = backend

        self.account_model.search.return_value = None
        self.account_model.create.return_value = new_account

        self.processor._handle_account_created(self.webhook_event, payload_data)

        self.account_model.create.assert_called_once()
        # Since sync_required is True and no with_delay, sync should be called directly on backend
        backend.sync_transactions_v2.assert_called_once_with(account_ids=[new_account.id])

    def test_handle_account_created_already_exists(self):
        """Test accounts.created when account already exists."""
        payload_data = {
            "data": {"id": "acc_existing", "name": "Existing Account", "balance": 2000.00}
        }

        existing_account = Mock()
        existing_account.id = 4
        existing_account.name = "Existing Account"

        self.account_model.search.return_value = existing_account

        with patch.object(self.processor, "_update_account_from_data") as mock_update:
            self.processor._handle_account_created(self.webhook_event, payload_data)

            mock_update.assert_called_once_with(existing_account, payload_data["data"])

    def test_handle_account_updated(self):
        """Test accounts.updated webhook processing."""
        payload_data = {
            "data": {
                "id": "acc_update",
                "name": "Updated Account",
                "balance": 5000.00,
                "balance_changed": True,
            }
        }

        account = Mock()
        account.id = 5
        account.name = "Account to Update"

        backend = Mock()
        backend.id = 1
        backend.with_delay = Mock()
        backend.with_delay.return_value.sync_transactions_v2 = Mock()
        self.webhook_event.backend_id = backend

        self.account_model.search.return_value = account

        with patch.object(self.processor, "_update_account_from_data") as mock_update:
            self.processor._handle_account_updated(self.webhook_event, payload_data)

            mock_update.assert_called_once()
            backend.with_delay.assert_called_once()

    def test_handle_transaction_created(self):
        """Test transactions.created webhook processing."""
        payload_data = {
            "data": {
                "id": "tr_new",
                "account_id": "acc_123",
                "description": "New Transaction",
                "amount": -50.00,
                "date": "2023-08-27T10:30:00Z",
                "status": "pending",
                "category": "Food",
                "merchant_name": "Restaurant ABC",
            }
        }

        account = Mock()
        account.id = 6
        account.name = "Account 123"

        new_transaction = Mock()
        new_transaction.id = 1
        new_transaction.name = "New Transaction"

        self.account_model.search.return_value = account
        self.transaction_model.search.return_value = None
        self.transaction_model.create.return_value = new_transaction

        self.processor._handle_transaction_created(self.webhook_event, payload_data)

        self.transaction_model.create.assert_called_once()

    def test_handle_transaction_updated(self):
        """Test transactions.updated webhook processing."""
        payload_data = {
            "data": {
                "id": "tr_update",
                "status": "completed",
                "amount": -75.00,
                "description": "Updated Description",
                "category": "Entertainment",
            }
        }

        transaction = Mock()
        transaction.id = 2
        transaction.name = "Transaction to Update"
        transaction.write = Mock()

        self.transaction_model.search.return_value = transaction

        self.processor._handle_transaction_updated(self.webhook_event, payload_data)

        transaction.write.assert_called_once()
        write_vals = transaction.write.call_args[0][0]
        self.assertEqual(write_vals["status"], "completed")
        self.assertEqual(write_vals["amount"], -75.00)

    def test_retry_logic(self):
        """Test webhook retry scheduling."""
        self.webhook_event.retry_count = 1
        self.webhook_event.event_id = "evt_retry"
        self.webhook_event.with_delay = Mock()
        self.webhook_event.with_delay.return_value.process_webhook = Mock()

        from unittest.mock import patch

        with patch("components.webhook_processor.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 8, 27, 10, 0, 0)
            mock_datetime.fromisoformat = datetime.fromisoformat

            self.processor._schedule_retry(self.webhook_event)

            self.webhook_event.with_delay.assert_called_once()

            kwargs = self.webhook_event.with_delay.call_args[1]
            eta = kwargs.get("eta")
            # Second retry should have 5 minute delay (300 seconds)
            expected_eta = datetime(2023, 8, 27, 10, 0, 0) + timedelta(seconds=300)
            self.assertEqual(eta, expected_eta)

    def test_should_retry(self):
        """Test retry decision logic."""
        self.webhook_event.retry_count = 0
        self.assertTrue(self.processor._should_retry(self.webhook_event))

        self.webhook_event.retry_count = 2
        self.assertTrue(self.processor._should_retry(self.webhook_event))

        self.webhook_event.retry_count = 3
        self.assertFalse(self.processor._should_retry(self.webhook_event))

    def test_process_pending_events(self):
        """Test batch processing of pending events."""
        event1 = Mock()
        event1.id = 1
        event2 = Mock()
        event2.id = 2
        event3 = Mock()
        event3.id = 3

        self.webhook_event_model.search.return_value = [event1, event2, event3]

        with patch.object(self.processor, "process_event") as mock_process:
            mock_process.side_effect = [True, False, True]

            result = self.processor.process_pending_events(limit=10)

            self.assertEqual(result["processed"], 2)
            self.assertEqual(result["failed"], 1)
            self.assertEqual(mock_process.call_count, 3)

    def test_prepare_account_values(self):
        """Test account value preparation from webhook data."""
        data = {
            "id": "acc_test",
            "name": "Test Account",
            "type": "checking",
            "balance": 1500.00,
            "currency": "EUR",
            "institution_name": "Test Bank EU",
            "active": True,
            "sync_required": True,
        }

        values = self.processor._prepare_account_values(data, self.backend)

        self.assertEqual(values["tesote_id"], "acc_test")
        self.assertEqual(values["name"], "Test Account")
        self.assertEqual(values["account_type"], "checking")
        self.assertEqual(values["balance"], 1500.00)
        self.assertEqual(values["currency"], "EUR")
        self.assertEqual(values["institution_name"], "Test Bank EU")
        self.assertTrue(values["active"])
        self.assertIsNotNone(values["last_sync"])

    def test_prepare_transaction_values(self):
        """Test transaction value preparation from webhook data."""
        account = Mock()
        account.id = 10

        data = {
            "id": "tr_test",
            "description": "Test Transaction",
            "amount": -25.50,
            "date": "2023-08-27T15:30:00Z",
            "status": "completed",
            "category": "Shopping",
            "merchant_name": "Store XYZ",
            "type": "debit",
        }

        values = self.processor._prepare_transaction_values(data, account)

        self.assertEqual(values["tesote_id"], "tr_test")
        self.assertEqual(values["account_id"], 10)
        self.assertEqual(values["name"], "Test Transaction")
        self.assertEqual(values["amount"], -25.50)
        self.assertEqual(values["status"], "completed")
        self.assertEqual(values["category"], "Shopping")
        self.assertEqual(values["merchant_name"], "Store XYZ")

    def test_update_account_from_data(self):
        """Test updating account from webhook data."""
        account = Mock()
        account.name = "Old Name"
        account.balance = 100.00
        account.account_type = "checking"
        account.institution_name = "Old Bank"
        account.active = True
        account.write = Mock()

        data = {
            "name": "New Name",
            "balance": 200.00,
            "type": "savings",
            "institution_name": "New Bank",
            "active": False,
        }

        self.processor._update_account_from_data(account, data)

        account.write.assert_called_once()
        update_vals = account.write.call_args[0][0]

        self.assertEqual(update_vals["name"], "New Name")
        self.assertEqual(update_vals["balance"], 200.00)
        self.assertEqual(update_vals["account_type"], "savings")
        self.assertEqual(update_vals["institution_name"], "New Bank")
        self.assertFalse(update_vals["active"])

    def test_fetch_and_create_account(self):
        """Test fetching account from API and creating it."""
        account_id = "acc_fetch"

        self.backend.api_url = "https://api.tesote.com"
        self.backend.api_key = "test_api_key"

        new_account = Mock()
        new_account.id = 20

        self.account_model.create.return_value = new_account

        # Mock the TesoteAdapter import inside the method
        with patch("components.adapter.TesoteAdapter") as MockAdapter:
            mock_adapter = Mock()
            MockAdapter.return_value = mock_adapter
            mock_adapter._call_api.return_value = {
                "data": {
                    "id": "acc_fetch",
                    "name": "Fetched Account",
                    "type": "checking",
                    "balance": 3000.00,
                    "currency": "USD",
                    "institution_name": "API Bank",
                    "active": True,
                }
            }

            result = self.processor._fetch_and_create_account(account_id, self.backend)

            self.account_model.create.assert_called_once()
            create_vals = self.account_model.create.call_args[0][0]
            self.assertEqual(create_vals["tesote_id"], "acc_fetch")
            self.assertEqual(create_vals["name"], "Fetched Account")
            self.assertEqual(result, new_account)
