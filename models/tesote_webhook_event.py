import json
import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TesoteWebhookEvent(models.Model):
    _name = 'tesote.webhook.event'
    _description = 'Tesote Webhook Event'
    _order = 'received_at desc'
    _rec_name = 'event_id'

    event_id = fields.Char(
        string='Event ID',
        required=True,
        index=True,
        help='Unique ID from X-Tesote-Webhook-Id header'
    )
    event_type = fields.Char(
        string='Event Type',
        required=True,
        index=True,
        help='Type of webhook event (e.g., sync.updates_available)'
    )
    payload = fields.Text(
        string='Payload',
        required=True,
        help='Complete webhook payload as JSON'
    )
    headers = fields.Text(
        string='Headers',
        help='All webhook headers received as JSON'
    )
    signature = fields.Char(
        string='Signature',
        help='Webhook signature for verification audit'
    )
    timestamp = fields.Datetime(
        string='Webhook Timestamp',
        help='Timestamp from webhook payload'
    )
    received_at = fields.Datetime(
        string='Received At',
        default=fields.Datetime.now,
        required=True,
        help='When Odoo received the webhook'
    )
    processed_at = fields.Datetime(
        string='Processed At',
        help='When processing completed'
    )
    processing_started_at = fields.Datetime(
        string='Processing Started At',
        help='When processing began'
    )
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Status', default='pending', required=True, index=True)
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        help='Number of processing retry attempts'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Error details if processing failed'
    )
    sync_job_id = fields.Char(
        string='Sync Job ID',
        help='Reference to triggered sync job'
    )
    processing_duration = fields.Float(
        string='Processing Duration (ms)',
        help='Time taken to process webhook in milliseconds'
    )
    backend_id = fields.Many2one(
        'tesote.backend',
        string='Backend',
        required=True,
        ondelete='cascade'
    )
    ip_address = fields.Char(
        string='IP Address',
        help='IP address of webhook sender'
    )
    raw_body = fields.Text(
        string='Raw Body',
        help='Raw webhook request body for debugging'
    )

    _sql_constraints = [
        ('event_id_unique', 'UNIQUE(event_id)', 'Event ID must be unique for idempotency'),
    ]

    def log_webhook_receipt(self, request):
        """Log webhook receipt details from request."""
        self.ensure_one()
        try:
            self.headers = json.dumps(dict(request.httprequest.headers))
            self.raw_body = request.httprequest.data.decode('utf-8')
            self.received_at = fields.Datetime.now()
            if hasattr(request.httprequest, 'remote_addr'):
                self.ip_address = request.httprequest.remote_addr
        except Exception as e:
            _logger.warning(f"Error logging webhook receipt: {e}")

    def log_processing_start(self):
        """Log when processing starts."""
        self.ensure_one()
        self.processing_started_at = fields.Datetime.now()
        self.status = 'processing'
        _logger.info(f"Processing webhook {self.event_id} type {self.event_type}")

    def log_processing_complete(self):
        """Log when processing completes successfully."""
        self.ensure_one()
        self.processed_at = fields.Datetime.now()
        if self.processing_started_at:
            duration_delta = self.processed_at - self.processing_started_at
            self.processing_duration = duration_delta.total_seconds() * 1000
            _logger.info(f"Completed webhook {self.event_id} in {self.processing_duration:.2f}ms")
        self.status = 'completed'

    def log_processing_error(self, error):
        """Log processing error details."""
        self.ensure_one()
        self.error_message = str(error)
        self.status = 'failed'
        self.retry_count += 1
        _logger.error(f"Failed webhook {self.event_id}: {error}", exc_info=True)

    @api.model
    def check_idempotency(self, event_id):
        """Check if event has already been processed (idempotency)."""
        existing = self.search([
            ('event_id', '=', event_id),
            ('status', 'in', ['completed', 'processing'])
        ], limit=1)
        return bool(existing)

    @api.model
    def cleanup_old_events(self, days=90):
        """Remove webhook events older than specified days."""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_events = self.search([('received_at', '<', cutoff_date)])
        count = len(old_events)
        old_events.unlink()
        _logger.info(f"Cleaned up {count} webhook events older than {days} days")
        return count

    def retry_failed_event(self):
        """Retry processing of a failed webhook event."""
        self.ensure_one()
        if self.status != 'failed':
            raise UserError(_('Can only retry failed webhook events'))
        
        self.status = 'pending'
        self.error_message = False
        _logger.info(f"Retrying webhook event {self.event_id} (attempt {self.retry_count + 1})")
        
        return True

    def get_payload_data(self):
        """Parse and return the payload data as dictionary."""
        self.ensure_one()
        try:
            return json.loads(self.payload)
        except (json.JSONDecodeError, TypeError) as e:
            _logger.error(f"Failed to parse webhook payload: {e}")
            return {}

    @api.model
    def get_statistics(self, hours=24):
        """Get webhook statistics for monitoring dashboard."""
        from datetime import timedelta
        cutoff = fields.Datetime.now() - timedelta(hours=hours)
        
        domain = [('received_at', '>=', cutoff)]
        events = self.search(domain)
        
        stats = {
            'total_received': len(events),
            'by_status': {},
            'by_type': {},
            'average_duration': 0,
            'failure_rate': 0,
        }
        
        for status in ['pending', 'processing', 'completed', 'failed']:
            stats['by_status'][status] = len(events.filtered(lambda e: e.status == status))
        
        event_types = events.mapped('event_type')
        for event_type in set(event_types):
            stats['by_type'][event_type] = len(events.filtered(lambda e: e.event_type == event_type))
        
        completed = events.filtered(lambda e: e.status == 'completed' and e.processing_duration)
        if completed:
            stats['average_duration'] = sum(completed.mapped('processing_duration')) / len(completed)
        
        if events:
            stats['failure_rate'] = (stats['by_status'].get('failed', 0) / len(events)) * 100
        
        return stats

    def process_webhook(self):
        """Process the webhook event based on its type."""
        self.ensure_one()
        
        try:
            self.log_processing_start()
            
            # Get payload data
            payload_data = self.get_payload_data()
            
            if self.event_type == 'sync.updates_available':
                self._process_sync_updates_available(payload_data)
            elif self.event_type == 'accounts.created':
                self._process_account_created(payload_data)
            elif self.event_type == 'accounts.updated':
                self._process_account_updated(payload_data)
            elif self.event_type == 'transactions.created':
                self._process_transaction_created(payload_data)
            elif self.event_type == 'transactions.updated':
                self._process_transaction_updated(payload_data)
            else:
                _logger.warning(f"Unknown webhook event type: {self.event_type}")
                self.log_processing_error(f"Unknown event type: {self.event_type}")
                return False
            
            self.log_processing_complete()
            return True
            
        except Exception as e:
            self.log_processing_error(str(e))
            return False

    def _process_sync_updates_available(self, payload_data):
        """
        Process sync.updates_available webhook event.
        This triggers a background sync job for the specified account.
        """
        try:
            # Extract account_id from payload
            data = payload_data.get('data', {})
            account_id = data.get('id')
            
            if not account_id:
                raise ValueError("Missing account ID in webhook payload")
            
            # Find corresponding tesote account
            TesoteAccount = self.env['tesote.account'].sudo()
            account = TesoteAccount.search([
                ('external_id', '=', account_id),
                ('backend_id', '=', self.backend_id.id)
            ], limit=1)
            
            if not account:
                _logger.warning(f"Account {account_id} not found for sync webhook")
                # Could create the account here if needed
                return
            
            # Log sync details
            new_count = data.get('new_transactions', 0)
            modified_count = data.get('modified_transactions', 0)
            removed_count = data.get('removed_transactions', 0)
            
            _logger.info(
                f"Sync updates available for account {account_id}: "
                f"new={new_count}, modified={modified_count}, removed={removed_count}"
            )
            
            # Trigger background sync for this account
            # Check if queue_job is available
            if hasattr(account, 'with_delay'):
                # Use queue_job for async sync
                job = account.with_delay(
                    description=f"Sync transactions for account {account.name}"
                ).sync_transactions()
                if hasattr(job, 'uuid'):
                    self.sync_job_id = str(job.uuid)
            else:
                # Direct sync (fallback)
                account.sync_transactions()
            
            _logger.info(f"Triggered sync for account {account_id} via webhook {self.event_id}")
            
        except Exception as e:
            _logger.error(f"Error processing sync.updates_available webhook: {e}")
            raise

    def _process_account_created(self, payload_data):
        """Process accounts.created webhook event."""
        try:
            data = payload_data.get('data', {})
            account_id = data.get('id')
            
            if not account_id:
                raise ValueError("Missing account ID in webhook payload")
            
            # Check if account already exists
            TesoteAccount = self.env['tesote.account'].sudo()
            existing = TesoteAccount.search([
                ('external_id', '=', account_id),
                ('backend_id', '=', self.backend_id.id)
            ], limit=1)
            
            if existing:
                _logger.info(f"Account {account_id} already exists, skipping creation")
                return
            
            # Create new account
            account_vals = {
                'external_id': account_id,
                'backend_id': self.backend_id.id,
                'name': data.get('name', f'Account {account_id}'),
                'account_type': data.get('type', 'checking'),
                'balance': data.get('balance', 0.0),
                'currency': data.get('currency', 'USD'),
                'institution_name': data.get('institution_name', ''),
                'active': data.get('active', True),
            }
            
            new_account = TesoteAccount.create(account_vals)
            _logger.info(f"Created account {new_account.name} from webhook")
            
        except Exception as e:
            _logger.error(f"Error processing accounts.created webhook: {e}")
            raise

    def _process_account_updated(self, payload_data):
        """Process accounts.updated webhook event."""
        try:
            data = payload_data.get('data', {})
            account_id = data.get('id')
            
            if not account_id:
                raise ValueError("Missing account ID in webhook payload")
            
            # Find existing account
            TesoteAccount = self.env['tesote.account'].sudo()
            account = TesoteAccount.search([
                ('external_id', '=', account_id),
                ('backend_id', '=', self.backend_id.id)
            ], limit=1)
            
            if not account:
                _logger.warning(f"Account {account_id} not found for update webhook")
                # Could create the account here if needed
                return
            
            # Update account fields
            update_vals = {}
            if 'name' in data:
                update_vals['name'] = data['name']
            if 'balance' in data:
                update_vals['balance'] = data['balance']
            if 'type' in data:
                update_vals['account_type'] = data['type']
            if 'institution_name' in data:
                update_vals['institution_name'] = data['institution_name']
            if 'active' in data:
                update_vals['active'] = data['active']
            
            if update_vals:
                account.write(update_vals)
                _logger.info(f"Updated account {account.name} from webhook")
            
        except Exception as e:
            _logger.error(f"Error processing accounts.updated webhook: {e}")
            raise

    def _process_transaction_created(self, payload_data):
        """Process transactions.created webhook event."""
        _logger.info("Processing transactions.created webhook (not yet implemented)")
        # This would create a new transaction record
        pass

    def _process_transaction_updated(self, payload_data):
        """Process transactions.updated webhook event."""
        _logger.info("Processing transactions.updated webhook (not yet implemented)")
        # This would update an existing transaction record
        pass
