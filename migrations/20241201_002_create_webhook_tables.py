# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Migration: Create Webhook Tables
Generated: 2024-12-01
Description: Creates webhook-related tables for real-time event processing
"""

try:
    from .framework import BaseMigration
except ImportError:
    # Fallback for testing
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from framework import BaseMigration


class CreateWebhookTables(BaseMigration):
    version = "20241201_002"
    description = "Create webhook tables for real-time event processing"
    
    def up(self):
        """Create webhook tables"""
        
        # 1. Webhook configuration table (singleton, like backend)
        self.create_table('tesote_webhook_config', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('backend_id', 'INTEGER NOT NULL REFERENCES tesote_backend(id) ON DELETE CASCADE'),
            ('webhook_url', 'VARCHAR(255)'),
            ('webhook_path', 'VARCHAR(255) DEFAULT \'/tesote/webhook\''),
            ('secret_key', 'VARCHAR(255) NOT NULL'),
            ('enabled', 'BOOLEAN DEFAULT FALSE'),
            
            # Event subscriptions
            ('subscribe_sync_updates', 'BOOLEAN DEFAULT TRUE'),
            ('subscribe_account_created', 'BOOLEAN DEFAULT TRUE'),
            ('subscribe_account_updated', 'BOOLEAN DEFAULT TRUE'),
            ('subscribe_transaction_created', 'BOOLEAN DEFAULT FALSE'),
            ('subscribe_transaction_updated', 'BOOLEAN DEFAULT FALSE'),
            
            # Monitoring fields
            ('last_webhook_at', 'TIMESTAMP'),
            ('total_webhooks_received', 'INTEGER DEFAULT 0'),
            ('failed_signature_count', 'INTEGER DEFAULT 0'),
            ('last_verified', 'TIMESTAMP'),
            ('verification_status', 'VARCHAR(50) DEFAULT \'pending\''),
            ('last_error', 'TEXT'),
            
            # Alert configuration
            ('alert_on_failure', 'BOOLEAN DEFAULT FALSE'),
            ('alert_threshold', 'DECIMAL(5,2) DEFAULT 10.0'),
            ('alert_email_to', 'VARCHAR(255)'),
            
            # Retry configuration  
            ('retry_max_attempts', 'INTEGER DEFAULT 3'),
            ('retry_backoff_base', 'DECIMAL(5,2) DEFAULT 2.0'),
            ('timeout_seconds', 'INTEGER DEFAULT 30'),
        ], indexes=[
            {'columns': ['backend_id'], 'unique': True},  # One config per backend
            {'columns': ['enabled'], 'unique': False},
        ])
        
        # 2. Webhook event types table
        self.create_table('tesote_webhook_event_type', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('name', 'VARCHAR(255) NOT NULL'),
            ('description', 'TEXT'),
            ('active', 'BOOLEAN DEFAULT TRUE'),
        ], indexes=[
            {'columns': ['name'], 'unique': True},
            {'columns': ['active'], 'unique': False},
        ])
        
        # 3. Webhook events table (audit trail)
        self.create_table('tesote_webhook_event', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('webhook_config_id', 'INTEGER REFERENCES tesote_webhook_config(id) ON DELETE CASCADE'),
            ('backend_id', 'INTEGER NOT NULL REFERENCES tesote_backend(id) ON DELETE CASCADE'),
            ('event_id', 'VARCHAR(255) NOT NULL'),  # From X-Tesote-Webhook-Id header
            ('event_type', 'VARCHAR(255) NOT NULL'),
            ('payload', 'TEXT'),
            ('headers', 'TEXT'),  # JSON
            ('signature', 'VARCHAR(255)'),
            ('timestamp', 'VARCHAR(50)'),  # From webhook header
            ('signature_valid', 'BOOLEAN'),
            ('ip_address', 'VARCHAR(45)'),
            
            # Processing fields
            ('status', 'VARCHAR(50) DEFAULT \'pending\''),  # pending, processing, completed, failed
            ('received_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('processed_at', 'TIMESTAMP'),
            ('processing_duration', 'INTEGER'),  # milliseconds
            ('retry_count', 'INTEGER DEFAULT 0'),
            ('error_message', 'TEXT'),
            ('sync_job_id', 'VARCHAR(255)'),  # If this event triggered a sync job
        ], indexes=[
            {'columns': ['event_id'], 'unique': True},  # Idempotency
            {'columns': ['webhook_config_id'], 'unique': False},
            {'columns': ['backend_id'], 'unique': False},
            {'columns': ['event_type'], 'unique': False},
            {'columns': ['status'], 'unique': False},
            {'columns': ['received_at'], 'unique': False},
            {'columns': ['signature_valid'], 'unique': False},
        ])
        
        # 4. Webhook monitoring table (aggregated stats)
        self.create_table('tesote_webhook_monitor', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('webhook_config_id', 'INTEGER REFERENCES tesote_webhook_config(id) ON DELETE CASCADE'),
            ('date', 'DATE NOT NULL'),
            ('total_received', 'INTEGER DEFAULT 0'),
            ('total_processed', 'INTEGER DEFAULT 0'),
            ('total_failed', 'INTEGER DEFAULT 0'),
            ('avg_processing_time', 'DECIMAL(10,2) DEFAULT 0'),
            ('signature_failures', 'INTEGER DEFAULT 0'),
            ('retry_attempts', 'INTEGER DEFAULT 0'),
        ], indexes=[
            {'columns': ['webhook_config_id', 'date'], 'unique': True},
            {'columns': ['date'], 'unique': False},
        ])
        
        # 5. Webhook secret wizard (transient model for UI)
        self.create_table('tesote_webhook_secret_wizard', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('webhook_config_id', 'INTEGER REFERENCES tesote_webhook_config(id) ON DELETE CASCADE'),
            ('secret_key', 'TEXT'),
            ('webhook_url', 'VARCHAR(255)'),
            ('instructions', 'TEXT'),
        ])
    
    def down(self):
        """Drop webhook tables in reverse order"""
        self.drop_table('tesote_webhook_secret_wizard')
        self.drop_table('tesote_webhook_monitor') 
        self.drop_table('tesote_webhook_event')
        self.drop_table('tesote_webhook_event_type')
        self.drop_table('tesote_webhook_config')
    
    def seed_data(self):
        """Add webhook event types"""
        event_types = [
            {
                'name': 'sync.updates_available',
                'description': 'Triggered when new transaction data is available for sync',
                'active': True
            },
            {
                'name': 'accounts.created',
                'description': 'New account created in tesote.com',
                'active': True
            },
            {
                'name': 'accounts.updated', 
                'description': 'Account details updated (balance, name, etc.)',
                'active': True
            },
            {
                'name': 'transactions.created',
                'description': 'New transaction added (real-time)',
                'active': True
            },
            {
                'name': 'transactions.updated',
                'description': 'Transaction status changed (pending → completed)',
                'active': True
            },
            {
                'name': 'test.webhook',
                'description': 'Test webhook event for configuration verification',
                'active': True
            },
        ]
        
        self.insert_data('tesote_webhook_event_type', event_types)