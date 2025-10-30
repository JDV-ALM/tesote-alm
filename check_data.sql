-- Check what data exists in all tesote_connector tables
-- Run this before uninstalling to see what will be deleted

SELECT 'tesote_backend' as table_name, COUNT(*) as record_count FROM tesote_backend
UNION ALL
SELECT 'tesote_account', COUNT(*) FROM tesote_account
UNION ALL
SELECT 'tesote_transaction', COUNT(*) FROM tesote_transaction
UNION ALL
SELECT 'tesote_sync_log', COUNT(*) FROM tesote_sync_log
UNION ALL
SELECT 'tesote_webhook_config', COUNT(*) FROM tesote_webhook_config
UNION ALL
SELECT 'tesote_webhook_event', COUNT(*) FROM tesote_webhook_event
UNION ALL
SELECT 'tesote_webhook_event_type', COUNT(*) FROM tesote_webhook_event_type
UNION ALL
SELECT 'tesote_webhook_monitor', COUNT(*) FROM tesote_webhook_monitor
UNION ALL
SELECT 'tesote_webhook_secret_wizard', COUNT(*) FROM tesote_webhook_secret_wizard
ORDER BY record_count DESC;
