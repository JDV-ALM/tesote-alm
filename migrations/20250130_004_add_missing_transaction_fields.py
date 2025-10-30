# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Migration: Add Missing Transaction Fields
Generated: 2025-01-30
Description: Adds fields that were added to tesote_transaction model after initial migration
"""

try:
    from ..migration_framework import BaseMigration
except ImportError:
    # Fallback for testing
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from migration_framework import BaseMigration


class AddMissingTransactionFields(BaseMigration):
    version = "20250130_004"
    description = "Add missing fields to tesote_transaction table"

    def up(self):
        """Add new fields to tesote_transaction table"""

        # 1. Rename 'date' to 'transaction_date' to match model
        self.execute(
            """
            ALTER TABLE tesote_transaction
            RENAME COLUMN date TO transaction_date;
            """
        )

        # 2. Add backend_id (Many2one to tesote.backend)
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS backend_id INTEGER REFERENCES tesote_backend(id) ON DELETE CASCADE;
            """
        )

        # 3. Add currency_id (Many2one to res.currency) to replace string currency field
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS currency_id INTEGER REFERENCES res_currency(id);
            """
        )

        # 4. Add categories field (renamed from category)
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS categories VARCHAR(255);
            """
        )

        # 5. Migrate data from category to categories if category exists
        self.execute(
            """
            UPDATE tesote_transaction
            SET categories = category
            WHERE category IS NOT NULL AND categories IS NULL;
            """
        )

        # 6. Add transaction_data field for JSON storage
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS transaction_data TEXT;
            """
        )

        # 7. Add tesote_imported_at timestamp
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS tesote_imported_at TIMESTAMP;
            """
        )

        # 8. Add tesote_updated_at timestamp
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS tesote_updated_at TIMESTAMP;
            """
        )

        # 9. Add account_move_id for Odoo accounting integration
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS account_move_id INTEGER REFERENCES account_move(id);
            """
        )

        # 10. Add is_reconciled boolean
        self.execute(
            """
            ALTER TABLE tesote_transaction
            ADD COLUMN IF NOT EXISTS is_reconciled BOOLEAN DEFAULT FALSE;
            """
        )

        # 11. Remove obsolete fields
        self.execute(
            """
            ALTER TABLE tesote_transaction
            DROP COLUMN IF EXISTS category;
            """
        )

        self.execute(
            """
            ALTER TABLE tesote_transaction
            DROP COLUMN IF EXISTS merchant_name;
            """
        )

        self.execute(
            """
            ALTER TABLE tesote_transaction
            DROP COLUMN IF EXISTS transaction_type;
            """
        )

        self.execute(
            """
            ALTER TABLE tesote_transaction
            DROP COLUMN IF EXISTS currency;
            """
        )

        self.execute(
            """
            ALTER TABLE tesote_transaction
            DROP COLUMN IF EXISTS external_reference;
            """
        )

        # 12. Create indexes for new fields
        self.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tesote_transaction_backend_id
            ON tesote_transaction(backend_id);
            """
        )

        self.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tesote_transaction_currency_id
            ON tesote_transaction(currency_id);
            """
        )

        self.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tesote_transaction_account_move_id
            ON tesote_transaction(account_move_id);
            """
        )

        self.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tesote_transaction_is_reconciled
            ON tesote_transaction(is_reconciled);
            """
        )

    def down(self):
        """Revert changes"""

        # Rename back
        self.execute(
            """
            ALTER TABLE tesote_transaction
            RENAME COLUMN transaction_date TO date;
            """
        )

        # Remove added fields
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS backend_id;")
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS currency_id;")
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS categories;")
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS transaction_data;")
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS tesote_imported_at;")
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS tesote_updated_at;")
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS account_move_id;")
        self.execute("ALTER TABLE tesote_transaction DROP COLUMN IF EXISTS is_reconciled;")

        # Re-add old fields
        self.execute(
            "ALTER TABLE tesote_transaction ADD COLUMN IF NOT EXISTS category VARCHAR(255);"
        )
        self.execute(
            "ALTER TABLE tesote_transaction ADD COLUMN IF NOT EXISTS merchant_name VARCHAR(255);"
        )
        self.execute(
            "ALTER TABLE tesote_transaction ADD COLUMN IF NOT EXISTS transaction_type VARCHAR(50) DEFAULT 'debit';"
        )
        self.execute(
            "ALTER TABLE tesote_transaction ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD';"
        )
        self.execute(
            "ALTER TABLE tesote_transaction ADD COLUMN IF NOT EXISTS external_reference VARCHAR(255);"
        )

    def seed_data(self):
        """No seed data needed"""
        pass
