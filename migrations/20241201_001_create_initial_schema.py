# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Migration: Create Initial Schema
Generated: 2024-12-01
Description: Creates core tables for tesote.com connector
"""

try:
    from ..migration_framework import BaseMigration
except ImportError:
    # Fallback for testing
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from migration_framework import BaseMigration


class CreateInitialSchema(BaseMigration):
    version = "20241201_001"
    description = "Create core tesote connector tables"
    
    def up(self):
        """Create core tables"""
        
        # 1. Backend configuration table (singleton)
        self.create_table('tesote_backend', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('name', 'VARCHAR(255) NOT NULL DEFAULT \'tesote.com\''),
            ('api_url', 'VARCHAR(255) NOT NULL'),
            ('api_token', 'TEXT NOT NULL'),
            ('rate_limit_tier', 'VARCHAR(50) DEFAULT \'standard\''),
            ('requests_per_minute', 'INTEGER DEFAULT 200'),
            ('company_id', 'INTEGER REFERENCES res_company(id)'),
            ('active', 'BOOLEAN DEFAULT TRUE'),
            ('last_sync_date', 'TIMESTAMP'),
        ], indexes=[
            {'columns': ['company_id'], 'unique': False},
            {'columns': ['active'], 'unique': False},
        ])
        
        # 2. Account table
        self.create_table('tesote_account', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('tesote_id', 'VARCHAR(255) NOT NULL'),
            ('backend_id', 'INTEGER NOT NULL REFERENCES tesote_backend(id) ON DELETE CASCADE'),
            ('name', 'VARCHAR(255) NOT NULL'),
            ('account_type', 'VARCHAR(50) DEFAULT \'checking\''),
            ('balance', 'DECIMAL(15,2) DEFAULT 0.0'),
            ('currency', 'VARCHAR(3) DEFAULT \'USD\''),
            ('institution_name', 'VARCHAR(255)'),
            ('bank_name', 'VARCHAR(255)'),
            ('account_number_masked', 'VARCHAR(50)'),
            ('legal_entity_name', 'VARCHAR(255)'),
            ('sync_cursor', 'TEXT'),
            ('last_sync', 'TIMESTAMP'),
            ('active', 'BOOLEAN DEFAULT TRUE'),
        ], indexes=[
            {'columns': ['tesote_id', 'backend_id'], 'unique': True},
            {'columns': ['backend_id'], 'unique': False},
            {'columns': ['active'], 'unique': False},
        ])
        
        # 3. Transaction table
        self.create_table('tesote_transaction', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('tesote_id', 'VARCHAR(255) NOT NULL'),
            ('account_id', 'INTEGER NOT NULL REFERENCES tesote_account(id) ON DELETE CASCADE'),
            ('name', 'TEXT NOT NULL'),
            ('date', 'DATE NOT NULL'),
            ('amount', 'DECIMAL(15,2) NOT NULL'),
            ('status', 'VARCHAR(50) DEFAULT \'pending\''),
            ('category', 'VARCHAR(255)'),
            ('merchant_name', 'VARCHAR(255)'),
            ('counterparty_name', 'VARCHAR(255)'),
            ('description', 'TEXT'),
            ('transaction_type', 'VARCHAR(50) DEFAULT \'debit\''),
            ('currency', 'VARCHAR(3) DEFAULT \'USD\''),
            ('external_reference', 'VARCHAR(255)'),
        ], indexes=[
            {'columns': ['tesote_id', 'account_id'], 'unique': True},
            {'columns': ['account_id'], 'unique': False},
            {'columns': ['date'], 'unique': False},
            {'columns': ['status'], 'unique': False},
            {'columns': ['amount'], 'unique': False},
        ])
        
        # 4. Sync log table
        self.create_table('tesote_sync_log', [
            ('id', 'SERIAL PRIMARY KEY'),
            ('backend_id', 'INTEGER NOT NULL REFERENCES tesote_backend(id) ON DELETE CASCADE'),
            ('operation', 'VARCHAR(100) NOT NULL'),
            ('status', 'VARCHAR(50) DEFAULT \'running\''),
            ('start_time', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('end_time', 'TIMESTAMP'),
            ('duration', 'INTEGER'),  # in milliseconds
            ('records_processed', 'INTEGER DEFAULT 0'),
            ('records_created', 'INTEGER DEFAULT 0'),
            ('records_updated', 'INTEGER DEFAULT 0'),
            ('records_failed', 'INTEGER DEFAULT 0'),
            ('error_message', 'TEXT'),
            ('sync_cursor_before', 'TEXT'),
            ('sync_cursor_after', 'TEXT'),
        ], indexes=[
            {'columns': ['backend_id'], 'unique': False},
            {'columns': ['operation'], 'unique': False},
            {'columns': ['status'], 'unique': False},
            {'columns': ['start_time'], 'unique': False},
        ])
    
    def down(self):
        """Drop core tables in reverse order"""
        self.drop_table('tesote_sync_log')
        self.drop_table('tesote_transaction')
        self.drop_table('tesote_account')
        self.drop_table('tesote_backend')
    
    def seed_data(self):
        """Add initial configuration data"""
        # No seed data for core tables - they'll be configured by user
        pass