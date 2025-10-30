# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Migration: Add Missing Account Fields
Generated: 2025-01-30
Description: Adds fields that were added to tesote_account model after initial migration
"""

try:
    from ..migration_framework import BaseMigration
except ImportError:
    # Fallback for testing
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from migration_framework import BaseMigration


class AddMissingAccountFields(BaseMigration):
    version = "20250130_003"
    description = "Add missing fields to tesote_account table"

    def up(self):
        """Add new fields to tesote_account table"""

        # Add fields that are in the model but missing from initial migration

        # 1. Add account_data field for JSON storage
        self.execute(
            """
            ALTER TABLE tesote_account
            ADD COLUMN IF NOT EXISTS account_data TEXT;
            """
        )

        # 2. Add currency_id (Many2one to res.currency)
        self.execute(
            """
            ALTER TABLE tesote_account
            ADD COLUMN IF NOT EXISTS currency_id INTEGER REFERENCES res_currency(id);
            """
        )

        # 3. Add tesote_created_at timestamp
        self.execute(
            """
            ALTER TABLE tesote_account
            ADD COLUMN IF NOT EXISTS tesote_created_at TIMESTAMP;
            """
        )

        # 4. Add tesote_updated_at timestamp
        self.execute(
            """
            ALTER TABLE tesote_account
            ADD COLUMN IF NOT EXISTS tesote_updated_at TIMESTAMP;
            """
        )

        # 5. Add balance_data_current_as_of timestamp
        # This field tracks when balance data was last updated in Tesote API
        self.execute(
            """
            ALTER TABLE tesote_account
            ADD COLUMN IF NOT EXISTS balance_data_current_as_of TIMESTAMP;
            """
        )

        # 6. Add partner_id (Many2one to res.partner)
        self.execute(
            """
            ALTER TABLE tesote_account
            ADD COLUMN IF NOT EXISTS partner_id INTEGER REFERENCES res_partner(id);
            """
        )

        # 7. Remove obsolete fields that were in migration but not in current model
        # Note: Only drop if they exist and are not being used
        self.execute(
            """
            ALTER TABLE tesote_account
            DROP COLUMN IF EXISTS account_type;
            """
        )

        self.execute(
            """
            ALTER TABLE tesote_account
            DROP COLUMN IF EXISTS currency;
            """
        )

        self.execute(
            """
            ALTER TABLE tesote_account
            DROP COLUMN IF EXISTS institution_name;
            """
        )

        self.execute(
            """
            ALTER TABLE tesote_account
            DROP COLUMN IF EXISTS account_number_masked;
            """
        )

        # 8. Create indexes for new fields
        self.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tesote_account_currency_id
            ON tesote_account(currency_id);
            """
        )

        self.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tesote_account_partner_id
            ON tesote_account(partner_id);
            """
        )

    def down(self):
        """Revert changes (remove added fields)"""

        # Remove added fields
        self.execute("ALTER TABLE tesote_account DROP COLUMN IF EXISTS account_data;")
        self.execute("ALTER TABLE tesote_account DROP COLUMN IF EXISTS currency_id;")
        self.execute("ALTER TABLE tesote_account DROP COLUMN IF EXISTS tesote_created_at;")
        self.execute("ALTER TABLE tesote_account DROP COLUMN IF EXISTS tesote_updated_at;")
        self.execute(
            "ALTER TABLE tesote_account DROP COLUMN IF EXISTS balance_data_current_as_of;"
        )
        self.execute("ALTER TABLE tesote_account DROP COLUMN IF EXISTS partner_id;")

        # Re-add the old fields if needed
        self.execute(
            "ALTER TABLE tesote_account ADD COLUMN IF NOT EXISTS account_type VARCHAR(50) DEFAULT 'checking';"
        )
        self.execute(
            "ALTER TABLE tesote_account ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD';"
        )
        self.execute(
            "ALTER TABLE tesote_account ADD COLUMN IF NOT EXISTS institution_name VARCHAR(255);"
        )
        self.execute(
            "ALTER TABLE tesote_account ADD COLUMN IF NOT EXISTS account_number_masked VARCHAR(50);"
        )

    def seed_data(self):
        """No seed data needed"""
        pass
