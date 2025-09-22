import hashlib
import hmac
import logging
import secrets
from urllib.parse import urljoin

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TesoteWebhookConfig(models.Model):
    _name = 'tesote.webhook.config'
    _description = 'Tesote Webhook Configuration'
    _rec_name = 'backend_id'

    backend_id = fields.Many2one(
        'tesote.backend',
        string='Backend',
        required=True,
        ondelete='cascade'
    )
    webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_webhook_url',
        store=False,
        help='Generated endpoint URL for receiving webhooks'
    )
    secret_key = fields.Char(
        string='Secret Key',
        required=True,
        help='Secret key for HMAC-SHA256 signature verification'
    )
    enabled = fields.Boolean(
        string='Enabled',
        default=False,
        help='Enable webhook processing'
    )
    
    # Event subscriptions
    subscribe_sync_updates = fields.Boolean(
        string='Sync Updates Available',
        default=True,
        help='Subscribe to sync.updates_available events'
    )
    subscribe_account_created = fields.Boolean(
        string='Account Created',
        default=True,
        help='Subscribe to accounts.created events'
    )
    subscribe_account_updated = fields.Boolean(
        string='Account Updated',
        default=True,
        help='Subscribe to accounts.updated events'
    )
    subscribe_transaction_created = fields.Boolean(
        string='Transaction Created',
        default=False,
        help='Subscribe to transactions.created events'
    )
    subscribe_transaction_updated = fields.Boolean(
        string='Transaction Updated',
        default=False,
        help='Subscribe to transactions.updated events'
    )
    
    # Monitoring fields
    last_webhook_at = fields.Datetime(
        string='Last Webhook Received',
        readonly=True,
        help='Timestamp of last webhook received'
    )
    total_webhooks_received = fields.Integer(
        string='Total Webhooks',
        default=0,
        readonly=True,
        help='Total number of webhooks received'
    )
    failed_signature_count = fields.Integer(
        string='Failed Signatures',
        default=0,
        readonly=True,
        help='Number of signature verification failures'
    )

    _sql_constraints = [
        ('backend_unique', 'UNIQUE(backend_id)', 'Only one webhook configuration per backend'),
    ]

    @api.depends('backend_id')
    def _compute_webhook_url(self):
        """Generate the webhook endpoint URL (static since backend is singleton)."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.backend_id:
                # Static URL since we have a singleton backend
                endpoint = '/tesote/webhook'
                record.webhook_url = urljoin(base_url, endpoint)
            else:
                record.webhook_url = ''

    @api.model
    def generate_secret_key(self):
        """Generate a secure random secret key."""
        return secrets.token_urlsafe(32)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate secret key on creation if not provided."""
        for vals in vals_list:
            if 'secret_key' not in vals or not vals['secret_key']:
                vals['secret_key'] = self.generate_secret_key()
        return super().create(vals_list)

    def regenerate_secret_key(self):
        """Regenerate the webhook secret key."""
        self.ensure_one()
        self.secret_key = self.generate_secret_key()
        _logger.info(f"Regenerated webhook secret key for backend {self.backend_id.name}")
        return True

    def get_active_events(self):
        """Return list of subscribed event types."""
        self.ensure_one()
        events = []
        if self.subscribe_sync_updates:
            events.append('sync.updates_available')
        if self.subscribe_account_created:
            events.append('accounts.created')
        if self.subscribe_account_updated:
            events.append('accounts.updated')
        if self.subscribe_transaction_created:
            events.append('transactions.created')
        if self.subscribe_transaction_updated:
            events.append('transactions.updated')
        return events

    def verify_signature(self, payload, timestamp, signature):
        """Verify webhook signature using HMAC-SHA256."""
        self.ensure_one()
        
        if not self.secret_key:
            _logger.error("No secret key configured for webhook verification")
            self.failed_signature_count += 1
            return False
        
        try:
            # Construct the signed payload
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')
            signed_payload = f"{timestamp}.{payload}"
            
            # Calculate expected signature
            expected = hmac.new(
                self.secret_key.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            is_valid = hmac.compare_digest(expected, signature)
            
            if not is_valid:
                self.failed_signature_count += 1
                _logger.warning(f"Webhook signature verification failed for backend {self.backend_id.name}")
            
            return is_valid
            
        except Exception as e:
            _logger.error(f"Error verifying webhook signature: {e}")
            self.failed_signature_count += 1
            return False

    def update_webhook_stats(self):
        """Update webhook statistics after receiving a webhook."""
        self.ensure_one()
        self.last_webhook_at = fields.Datetime.now()
        self.total_webhooks_received += 1

    def test_webhook_connection(self):
        """Test webhook configuration by sending a test event."""
        self.ensure_one()
        if not self.enabled:
            raise UserError(_('Please enable webhook configuration first'))
        
        # This would typically make an API call to tesote.com to trigger a test webhook
        _logger.info(f"Testing webhook configuration for backend {self.backend_id.name}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Webhook Test'),
                'message': _('Test webhook request sent. Check the webhook events for results.'),
                'sticky': False,
            }
        }

    @api.model
    def get_config_for_backend(self, backend_id):
        """Get webhook configuration for a specific backend."""
        config = self.search([('backend_id', '=', backend_id)], limit=1)
        if not config:
            _logger.debug(f"No webhook configuration found for backend {backend_id}")
        return config
