# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

tesote.com Odoo API Connector - Integration between Odoo 18.0 and tesote.com API v2.0.0 for financial data synchronization.

**Features**:
- Single API configuration (singleton pattern)
- Account and transaction synchronization  
- Cursor-based incremental sync
- Rate limiting support (Standard/Premium/Enterprise tiers)
- Webhook support for real-time updates
- Multi-language support (English/Spanish)

## Key Components

### API Adapter (`components/adapter.py`)
- Handles all communication with tesote.com API v2
- Key method: `sync_transactions()` - Uses v2 sync endpoint for cursor-based updates
- Rate limiting: 200 requests/minute (standard tier)

### Models
- `tesote_backend.py` - Backend configuration and sync orchestration
- `tesote_account.py` - Financial accounts with sync cursor tracking  
- `tesote_transaction.py` - Transactions with pending/completed status handling
- `tesote_binding.py` - Abstract base for all tesote.com models

### Components
- `binder.py` - Maps tesote.com IDs ↔ Odoo IDs
- `mapper.py` - Data transformation between formats
- `importer.py` - Handles sync response (added/modified/removed)
- `webhook_processor.py` - Handles real-time webhook event processing

### Webhooks
- `tesote_webhook_config.py` - Webhook configuration (singleton pattern)
- `tesote_webhook_event.py` - Webhook event records and processing
- `webhook_controller.py` - HTTP endpoint for receiving webhooks (`/tesote/webhook`)
- Real-time event processing with HMAC-SHA256 signature verification
- Supports sync triggers, account updates, transaction notifications

## Testing

The module includes unit tests that can run without Odoo installation by mocking Odoo dependencies.

### Running Tests Without Odoo

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_adapter_simple.py -v

# Run with coverage
python3 -m pytest tests/ --cov=components --cov-report=term-missing
```

### Test Structure

- `tests/conftest.py` - Mocks Odoo modules and dependencies
- `tests/test_adapter_simple.py` - Unit tests for API adapter
- Tests use `responses` library to mock HTTP calls
- All Odoo imports are mocked via conftest.py

### Mocked Odoo Components

The `conftest.py` file mocks:
- `odoo.models.Model` - Base model class
- `odoo.fields` - All field types (Char, Integer, etc.)
- `odoo.api` - Decorators (@api.model, @api.depends)
- `odoo.exceptions.UserError` - Exception classes
- `odoo._()` - Translation function

This allows running tests in any Python environment without Odoo installation.

## tesote.com API v2 Key Points

- **Sync Endpoint**: `POST /api/v2/transactions/sync` with cursor management
- **Transaction States**: `pending` → `completed` (36 business hours aging)
- **Sync Arrays**: Process in order: removed → modified → added
- **Cursor**: Always store `next_cursor` for incremental updates
- **Rate Limits**: 200/min standard, 500/min premium, 1000/min enterprise
- **Webhooks**: Real-time notifications for `sync.updates_available`, `accounts.created/updated`, `transactions.created/updated`

## Development Guidelines

1. **No v1 code** - Only v2 API is supported
2. **Test First** - TDD approach with pytest
3. **SOLID Principles** - Single responsibility, open/closed, etc.
4. **Cursor Management** - Always update and store cursors after sync
5. **Singleton Backend** - Only one backend configuration allowed
6. **Date Handling** - Convert ISO dates with timezone to Odoo format
7. **Webhook Security** - Always verify HMAC-SHA256 signatures and check idempotency

## Internationalization (i18n)

The module supports multiple languages with complete translations:

### Supported Languages
- **English** (en_US) - Default
- **Spanish** (es) - Full translation

### Translation Files
- `i18n/tesote_connector.pot` - Translation template
- `i18n/en_US.po` - English translations
- `i18n/es.po` - Spanish translations

### Key Translated Elements
- All menu items and navigation
- Button labels and actions
- Field labels and help text
- Error messages and notifications
- Status values and selections
- Search filters and groupings

### Adding New Translations
1. All user-facing strings in Python use `_()` function
2. XML view strings use `string` attribute (auto-translatable)
3. Update `.po` files when adding new strings
4. Test in target language via user preferences