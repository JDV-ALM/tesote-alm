# Sentry Error Tracking Integration

This document describes the Sentry error tracking integration for the tesote_connector Odoo module.

## Overview

The module includes automatic error tracking using Sentry.io with the following features:

- **Obfuscated DSN**: DSN is base64-encoded to avoid plain-text exposure in source code
- **Module-specific filtering**: Only captures errors originating from `tesote_connector` code
- **Automatic initialization**: Sentry is initialized when the Odoo module loads
- **Manual capture helpers**: Convenience functions for explicitly capturing exceptions and messages

## Automatic Error Capture

Sentry automatically captures all unhandled exceptions that occur within the `tesote_connector` module. No additional code is required - just install and use the module normally.

### What Gets Captured

- Errors in API communication (`components/adapter.py`)
- Model validation errors (`models/*.py`)
- Webhook processing errors (`components/webhook_processor.py`)
- Sync operation failures

### What Doesn't Get Captured

- Errors from other Odoo modules
- Errors from Odoo core
- Errors from third-party dependencies (unless called from our code)

## Manual Error Capture

For specific error scenarios where you want to explicitly send an error to Sentry:

```python
from odoo.addons.tesote_connector.utils.sentry_config import capture_exception

try:
    # Some risky operation
    result = api_call()
except Exception as e:
    # Log locally
    _logger.error(f"API call failed: {e}")

    # Also send to Sentry with additional context
    capture_exception(
        e,
        level="error",
        tags={
            "operation": "api_sync",
            "account_id": account.id,
        }
    )
    raise
```

## Manual Message Capture

To send informational messages or warnings to Sentry (useful for tracking important events):

```python
from odoo.addons.tesote_connector.utils.sentry_config import capture_message

# After a successful but noteworthy operation
capture_message(
    "Large sync completed successfully",
    level="info",
    tags={
        "accounts_synced": 150,
        "transactions_added": 5000,
    }
)
```

## Configuration

### DSN Obfuscation

The Sentry DSN is stored as a base64-encoded string in `utils/sentry_config.py`:

```python
_OBFUSCATED_DSN = "aHR0cHM6Ly8xMDNjNz..."
```

**Note**: This provides obfuscation, not security. The DSN can be decoded by anyone with access to the source code. However, Sentry DSNs are meant to be public-facing (they're used in client-side JavaScript), so this level of obfuscation is acceptable.

### Environment Configuration

You can customize the Sentry environment by editing `utils/sentry_config.py`:

```python
environment="production",  # Change to "staging" or "development"
```

### Changing the DSN

To update the DSN:

1. Get your new DSN from Sentry.io
2. Encode it to base64:
   ```python
   import base64
   dsn = "https://your-new-dsn@sentry.io/project"
   encoded = base64.b64encode(dsn.encode()).decode()
   print(encoded)
   ```
3. Update `_OBFUSCATED_DSN` in `utils/sentry_config.py`

## Event Filtering

The module uses a `before_send` hook to filter events. Only events with stack frames containing `tesote_connector` or `tesote-odoo-api-connector` in their file paths are sent to Sentry.

### Filter Logic

```python
def _should_capture_event(event, hint):
    # Checks exception traceback for tesote_connector frames
    # Returns event if found, None to drop
```

This ensures that:
- You only pay for errors from your code
- Sentry doesn't get flooded with unrelated errors
- Error reports are focused and actionable

## Testing

The integration includes comprehensive tests in `tests/test_sentry_config.py`:

```bash
# Run Sentry tests only
uv run pytest tests/test_sentry_config.py -v

# Run all tests (including Sentry)
uv run pytest
```

## Sentry Dashboard

All captured errors appear in your Sentry dashboard with:

- **Environment**: production/staging/development
- **Release**: tesote_connector@18.0.1.0.0
- **Tags**: module=tesote_connector, odoo_version=18.0
- **Context**: Request data, user info (if `send_default_pii=True`)

## Disabling Sentry

If you need to disable Sentry temporarily:

1. **For testing**: Tests automatically mock Sentry - no special configuration needed
2. **For production**: Remove or comment out the initialization in `__init__.py`
3. **Uninstall package**: Remove `sentry-sdk` from dependencies (module will still work)

## Performance Impact

Sentry is configured with:

- **Performance monitoring disabled**: `traces_sample_rate=0.0`
- **Minimal overhead**: Only active when exceptions occur
- **Async sending**: Doesn't block request handling

The performance impact should be negligible (<1ms per request in normal operation).

## Security Considerations

1. **DSN Exposure**: The DSN is obfuscated but not encrypted. This is acceptable since Sentry DSNs are designed to be public.
2. **PII Data**: `send_default_pii=True` includes request headers and user data. Review Sentry's data handling policies for compliance.
3. **Error Content**: Be careful not to log sensitive data (passwords, API keys) in error messages.

## Troubleshooting

### Sentry not capturing errors

1. Check that `sentry-sdk` is installed: `pip list | grep sentry`
2. Check Odoo logs for initialization message: "Sentry SDK initialized successfully"
3. Verify errors are from `tesote_connector` code (filtering may be dropping them)
4. Check Sentry.io dashboard for rate limits or quota issues

### Too many errors being captured

1. Review the `_should_capture_event` filter logic
2. Add additional filtering conditions as needed
3. Adjust Sentry's rate limiting in the dashboard

### DSN decode error

1. Verify `_OBFUSCATED_DSN` is valid base64
2. Check for line breaks or extra characters in the string
3. Re-encode the DSN following the instructions above

## Additional Resources

- [Sentry Python Documentation](https://docs.sentry.io/platforms/python/)
- [Sentry Error Filtering](https://docs.sentry.io/platforms/python/configuration/filtering/)
- [Sentry Data Management](https://docs.sentry.io/platforms/python/data-management/)
