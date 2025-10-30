# Migrations and Data Persistence Guide

## How Odoo Handles Module Installation/Uninstallation

### Module Installation
When you install the `tesote_connector` module:
1. **Odoo ORM creates tables automatically** based on model definitions (`_name`, field definitions)
2. **Custom migrations run** (if properly configured) to modify the schema
3. **Data files load** (XML files from `__manifest__.py` data section)
4. **Post-init hooks execute** (if defined in manifest)

### Module Uninstallation

**⚠️ CRITICAL: Uninstalling the module DELETES ALL DATA!**

When you uninstall the module, Odoo will:

1. **DROP ALL TABLES** for models defined in the module:
   - `tesote_backend` - **All backend configurations DELETED**
   - `tesote_account` - **All synced accounts DELETED**
   - `tesote_transaction` - **All synced transactions DELETED**
   - `tesote_sync_log` - **All sync history DELETED**
   - `tesote_webhook_config` - **All webhook configuration DELETED**
   - `tesote_webhook_event` - **All webhook event history DELETED**
   - `tesote_webhook_event_type` - **All event type definitions DELETED**
   - `tesote_webhook_monitor` - **All monitoring data DELETED**
   - `tesote_webhook_secret_wizard` - **All wizard data DELETED**

2. **Remove all related records**:
   - Menu items
   - Views
   - Security rules
   - Scheduled actions (crons)

3. **NO BACKUP IS CREATED** - Data is permanently lost unless you back it up manually

### How to Preserve Data

If you need to uninstall and reinstall (e.g., for testing), you have two options:

#### Option 1: Database Backup (Recommended for Production)
```bash
# Backup before uninstall
pg_dump -U odoo -d tesote_dev > backup_before_uninstall.sql

# After reinstall, restore data if needed
psql -U odoo -d tesote_dev < backup_before_uninstall.sql
```

#### Option 2: Upgrade Instead of Reinstall
Instead of uninstalling, upgrade the module to apply schema changes:
```python
# In Odoo
Apps → tesote.com Connector → Upgrade
```

This preserves data while applying new migrations.

## Migration System

This module uses a **custom migration framework** alongside Odoo's native ORM table creation.

### How Migrations Work

1. **Initial Install**: Odoo creates tables from model definitions (Python ORM)
2. **Upgrades**: Custom migrations in `/migrations/` folder run to modify schema
3. **Migration files** are executed in order based on version number (e.g., `20241201_001`, `20250130_003`)

### Current Migrations

| Version | File | Description |
|---------|------|-------------|
| `20241201_001` | `create_initial_schema.py` | Creates core tables (backend, account, transaction, sync_log) |
| `20241201_002` | `create_webhook_tables.py` | Creates webhook tables (config, events, monitoring) |
| `20250130_003` | `add_missing_account_fields.py` | Adds fields missing from initial migration (balance_data_current_as_of, etc.) |
| `20250130_004` | `add_missing_transaction_fields.py` | Updates transaction table to match current model |

### Schema Evolution

The initial migrations (`20241201_001` and `20241201_002`) created tables that didn't match the current model definitions. This happened because:

1. Models evolved over time (new fields added)
2. Migrations weren't updated to reflect model changes
3. Odoo's ORM creates tables differently than the migrations expected

**Result**: If you upgrade an existing installation, you need migrations `003` and `004` to add missing fields.

**If you do fresh install (or uninstall/reinstall)**: Odoo creates tables from current models, so all fields exist. But migrations are still good to have for consistency.

## Field Mapping Changes

### tesote_account Table

**Fields added after initial migration:**
- `account_data` (TEXT) - JSON data storage
- `currency_id` (INTEGER) - Reference to res.currency (replaced string `currency`)
- `tesote_created_at` (TIMESTAMP) - Account creation time in Tesote
- `tesote_updated_at` (TIMESTAMP) - Last update time in Tesote
- `balance_data_current_as_of` (TIMESTAMP) - Balance data timestamp ⭐ **Key for balance tracking**
- `partner_id` (INTEGER) - Reference to res.partner

**Fields removed:**
- `account_type` (VARCHAR) - No longer used
- `currency` (VARCHAR) - Replaced by `currency_id` Many2one
- `institution_name` (VARCHAR) - Not in current model
- `account_number_masked` (VARCHAR) - Not in current model

### tesote_transaction Table

**Fields added after initial migration:**
- `transaction_date` (DATE) - Renamed from `date`
- `backend_id` (INTEGER) - Reference to tesote.backend
- `currency_id` (INTEGER) - Reference to res.currency
- `categories` (VARCHAR) - Renamed from `category`
- `transaction_data` (TEXT) - JSON data storage
- `tesote_imported_at` (TIMESTAMP) - Import timestamp
- `tesote_updated_at` (TIMESTAMP) - Last update timestamp
- `account_move_id` (INTEGER) - Reference to account.move for reconciliation
- `is_reconciled` (BOOLEAN) - Reconciliation status

**Fields removed:**
- `category` (VARCHAR) - Renamed to `categories`
- `merchant_name` (VARCHAR) - Replaced by `counterparty_name`
- `transaction_type` (VARCHAR) - Not in current model
- `currency` (VARCHAR) - Replaced by `currency_id` Many2one
- `external_reference` (VARCHAR) - Not in current model

## Best Practices

### For Development
1. **Always use upgrades** instead of uninstall/reinstall when possible
2. **Test migrations** on a copy of production database first
3. **Create migrations** whenever you add/remove/rename model fields
4. **Use `IF NOT EXISTS` and `IF EXISTS`** clauses in migrations for safety

### For Production
1. **ALWAYS backup** before uninstalling or upgrading
2. **Test upgrade path** in staging environment first
3. **Document schema changes** in migration descriptions
4. **Monitor logs** during migration execution

### Creating New Migrations

When you add a new field to a model:

1. Update the model definition (`models/tesote_*.py`)
2. Create a migration file in `/migrations/` with next version number
3. Use the template:

```python
# migrations/YYYYMMDD_NNN_description.py
from ..migration_framework import BaseMigration

class MyMigration(BaseMigration):
    version = "YYYYMMDD_NNN"
    description = "Add new field to table"

    def up(self):
        self.execute(\"\"\"
            ALTER TABLE my_table
            ADD COLUMN IF NOT EXISTS my_field VARCHAR(255);
        \"\"\")

    def down(self):
        self.execute(\"\"\"
            ALTER TABLE my_table
            DROP COLUMN IF EXISTS my_field;
        \"\"\")

    def seed_data(self):
        pass
```

## Troubleshooting

### "Column does not exist" Error

**Symptom**: `ERROR: column tesote_account.balance_data_current_as_of does not exist`

**Cause**: You upgraded from an old version without running migrations, or installed before migrations were created.

**Solution**:
- **Option 1 (Safe)**: Upgrade the module to run migrations
- **Option 2 (Data Loss)**: Uninstall and reinstall (DELETES ALL DATA!)

### Migrations Not Running

**Check**:
1. Is the migration file in `/migrations/` folder?
2. Is the version number correct and sequential?
3. Check Odoo logs for migration execution messages

### Table Already Exists Error

**Symptom**: Migration fails because table already exists

**Solution**: Use `IF NOT EXISTS` in CREATE statements:
```sql
CREATE TABLE IF NOT EXISTS my_table (...);
```

## Summary

- ✅ **Migrations** help evolve schema over time
- ⚠️ **Uninstall DELETES ALL DATA** - always backup first
- 🔄 **Upgrade preserves data** - use this for schema changes
- 📝 **Document changes** in migration descriptions
- 🧪 **Test migrations** in staging before production
