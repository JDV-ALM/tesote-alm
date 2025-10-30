"""
Tests for webhook singleton configuration pattern.
"""

import unittest
from unittest.mock import MagicMock, patch


class TestWebhookConfigSingleton(unittest.TestCase):
    """Test webhook configuration singleton pattern."""

    def setUp(self):
        """Set up test fixtures."""
        self.env = MagicMock()
        self.backend = MagicMock()
        self.backend.id = 1
        self.backend.name = "Test Backend"

    def test_singleton_create_prevents_multiple_configs(self):
        """Test that only one webhook configuration can be created."""
        from models.tesote_webhook_config import TesoteWebhookConfig

        # Mock existing config search to return a result
        config = TesoteWebhookConfig()
        config.env = self.env
        config.search = MagicMock()
        config.search.return_value = [MagicMock()]  # Return existing config

        # Should raise UserError when trying to create second config
        from odoo.exceptions import UserError

        with patch("models.tesote_webhook_config.UserError", UserError):
            with self.assertRaises(UserError) as context:
                config.create([{"backend_id": 1}])

            self.assertIn("Only one webhook configuration is allowed", str(context.exception))

    def test_singleton_create_requires_backend(self):
        """Test that webhook configuration requires a backend."""
        from models.tesote_webhook_config import TesoteWebhookConfig

        # Mock no existing configs and no backend
        config = TesoteWebhookConfig()
        config.env = self.env
        config.search = MagicMock()
        config.search.return_value = []  # No existing configs

        # Mock backend search to return empty
        backend_mock = MagicMock()
        backend_mock.search.return_value = []
        config.env.__getitem__ = MagicMock(return_value=backend_mock)

        # Should raise UserError when no backend exists
        from odoo.exceptions import UserError

        with patch("models.tesote_webhook_config.UserError", UserError):
            with self.assertRaises(UserError) as context:
                config.create([{}])

            self.assertIn("No backend configuration found", str(context.exception))

    def test_action_open_configuration_creates_default(self):
        """Test that action_open_configuration creates default config if none exists."""
        from models.tesote_webhook_config import TesoteWebhookConfig

        config = TesoteWebhookConfig()
        config.env = self.env

        # Mock empty recordset for config search
        empty_recordset = MagicMock()
        empty_recordset.__bool__ = MagicMock(return_value=False)  # Makes "if not config:" work
        config.search = MagicMock(return_value=empty_recordset)
        config.create = MagicMock()

        # Mock backend recordset
        backend_recordset = MagicMock()
        backend_recordset.__bool__ = MagicMock(return_value=True)
        backend_recordset.id = self.backend.id
        backend_mock = MagicMock()
        backend_mock.search.return_value = backend_recordset
        config.env.__getitem__ = MagicMock(return_value=backend_mock)

        # Mock env.ref for view_id
        ref_mock = MagicMock()
        ref_mock.id = 123
        config.env.ref = MagicMock(return_value=ref_mock)

        # Mock created config
        created_config = MagicMock()
        created_config.id = 1
        config.create.return_value = created_config

        result = config.action_open_configuration()

        # Should create config with default values
        config.create.assert_called_once()
        create_vals = config.create.call_args[0][0]
        self.assertEqual(create_vals["backend_id"], self.backend.id)
        self.assertFalse(create_vals["enabled"])
        self.assertTrue(create_vals["subscribe_sync_updates"])
        self.assertTrue(create_vals["subscribe_account_created"])

        # Should return proper action
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "tesote.webhook.config")
        self.assertEqual(result["res_id"], created_config.id)

    def test_action_open_configuration_existing_config(self):
        """Test that action_open_configuration opens existing config."""
        from models.tesote_webhook_config import TesoteWebhookConfig

        config = TesoteWebhookConfig()
        config.env = self.env

        # Mock existing config recordset
        existing_config = MagicMock()
        existing_config.__bool__ = MagicMock(return_value=True)  # Makes "if not config:" work
        existing_config.id = 1
        config.search = MagicMock(return_value=existing_config)
        config.create = MagicMock()  # Should not be called

        # Mock env.ref for view_id
        ref_mock = MagicMock()
        ref_mock.id = 123
        config.env.ref = MagicMock(return_value=ref_mock)

        result = config.action_open_configuration()

        # Should not create new config
        config.create.assert_not_called()

        # Should return action for existing config
        self.assertEqual(result["res_id"], existing_config.id)

    def test_webhook_config_auto_assigns_backend(self):
        """Test that webhook config automatically assigns singleton backend."""
        from models.tesote_webhook_config import TesoteWebhookConfig

        config = TesoteWebhookConfig()
        config.env = self.env

        # Mock empty recordset for config search (no existing configs)
        empty_recordset = MagicMock()
        empty_recordset.__bool__ = MagicMock(return_value=False)
        config.search = MagicMock(return_value=empty_recordset)
        config.generate_secret_key = MagicMock(return_value="test_secret")

        # Mock backend recordset
        backend_recordset = MagicMock()
        backend_recordset.__bool__ = MagicMock(return_value=True)
        backend_recordset.id = self.backend.id
        backend_mock = MagicMock()
        backend_mock.search.return_value = backend_recordset
        config.env.__getitem__ = MagicMock(return_value=backend_mock)

        # Mock super().create
        with patch("models.tesote_webhook_config.super") as mock_super:
            mock_super.return_value.create.return_value = MagicMock()

            # Create without backend_id
            config.create([{}])

            # Should have added backend_id to vals
            create_call = mock_super.return_value.create.call_args[0][0]
            self.assertEqual(create_call[0]["backend_id"], self.backend.id)
            self.assertEqual(create_call[0]["secret_key"], "test_secret")


if __name__ == "__main__":
    unittest.main()
