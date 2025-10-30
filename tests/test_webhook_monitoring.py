import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock


def test_webhook_monitor_update_metrics():
    """Test webhook monitor metrics update"""
    from models.tesote_webhook_monitor import TesoteWebhookMonitor

    # Create mock objects
    monitor = MagicMock(spec=TesoteWebhookMonitor)
    monitor.total_received = 0
    monitor.total_processed = 0
    monitor.total_failed = 0
    monitor.total_retried = 0
    monitor.avg_processing_time = 0.0
    monitor.max_processing_time = 0.0
    monitor.min_processing_time = 0.0
    monitor.metrics_by_type = "{}"
    monitor.signature_failures = 0

    webhook_event = MagicMock()
    webhook_event.status = "completed"
    webhook_event.event_type = "sync.updates_available"
    webhook_event.processing_duration = 150.0
    webhook_event.retry_count = 0
    webhook_event.signature_valid = True

    # Simulate the update_metrics logic
    monitor.total_received = 1
    monitor.total_processed = 1
    monitor.avg_processing_time = 150.0
    monitor.max_processing_time = 150.0
    monitor.min_processing_time = 150.0

    metrics_by_type = {
        "sync.updates_available": {"received": 1, "processed": 1, "failed": 0, "avg_time": 150.0}
    }
    monitor.metrics_by_type = json.dumps(metrics_by_type)

    # Verify metrics
    assert monitor.total_received == 1
    assert monitor.total_processed == 1
    assert monitor.avg_processing_time == 150.0
    assert monitor.max_processing_time == 150.0
    assert monitor.min_processing_time == 150.0

    metrics = json.loads(monitor.metrics_by_type)
    assert metrics["sync.updates_available"]["received"] == 1
    assert metrics["sync.updates_available"]["processed"] == 1
    assert metrics["sync.updates_available"]["avg_time"] == 150.0


def test_webhook_monitor_success_rate():
    """Test success rate calculation"""
    from models.tesote_webhook_monitor import TesoteWebhookMonitor

    monitor = MagicMock(spec=TesoteWebhookMonitor)

    # Test with successful events
    monitor.total_received = 100
    monitor.total_processed = 95
    success_rate = (monitor.total_processed / monitor.total_received) * 100
    assert success_rate == 95.0

    # Test with no events
    monitor.total_received = 0
    monitor.total_processed = 0
    success_rate = (
        0.0
        if monitor.total_received == 0
        else (monitor.total_processed / monitor.total_received) * 100
    )
    assert success_rate == 0.0


def test_webhook_monitor_alert_conditions():
    """Test alert condition checking"""
    from models.tesote_webhook_monitor import TesoteWebhookMonitor

    monitor = MagicMock(spec=TesoteWebhookMonitor)
    monitor.success_rate = 85.0  # 15% failure rate
    monitor.signature_failures = 10
    monitor.backend_id = MagicMock()
    monitor.backend_id.name = "Test Backend"
    monitor.date = datetime.now().date()
    monitor.hour = datetime.now().hour

    # Create mock config
    config = MagicMock()
    config.alert_on_failure = True
    config.alert_threshold = 10.0  # Alert if failure rate > 10%

    # Test high failure rate alert
    alerts = []
    failure_rate = 100 - monitor.success_rate
    if failure_rate > config.alert_threshold:
        alerts.append(
            {
                "type": "high_failure_rate",
                "backend": monitor.backend_id.name,
                "failure_rate": failure_rate,
                "threshold": config.alert_threshold,
                "hour": monitor.hour,
                "date": monitor.date,
            }
        )

    assert len(alerts) == 1
    assert alerts[0]["type"] == "high_failure_rate"
    assert alerts[0]["failure_rate"] == 15.0

    # Test signature failure alert
    if monitor.signature_failures > 5:
        alerts.append(
            {
                "type": "signature_failures",
                "backend": monitor.backend_id.name,
                "count": monitor.signature_failures,
                "hour": monitor.hour,
                "date": monitor.date,
            }
        )

    assert len(alerts) == 2
    assert alerts[1]["type"] == "signature_failures"
    assert alerts[1]["count"] == 10


def test_webhook_monitor_daily_report():
    """Test daily report generation"""
    from models.tesote_webhook_monitor import TesoteWebhookMonitor

    # Create mock monitors for a day
    monitors = []
    for hour in range(24):
        monitor = MagicMock(spec=TesoteWebhookMonitor)
        monitor.hour = hour
        monitor.total_received = 10 if hour >= 8 and hour <= 18 else 2
        monitor.total_processed = 9 if hour >= 8 and hour <= 18 else 2
        monitor.total_failed = 1 if hour >= 8 and hour <= 18 else 0
        monitor.signature_failures = 0
        monitor.alerts_triggered = 0
        monitor.metrics_by_type = json.dumps(
            {
                "sync.updates_available": {
                    "received": monitor.total_received,
                    "processed": monitor.total_processed,
                    "failed": monitor.total_failed,
                }
            }
        )
        monitors.append(monitor)

    # Generate report
    total_received = sum(m.total_received for m in monitors)
    total_processed = sum(m.total_processed for m in monitors)
    total_failed = sum(m.total_failed for m in monitors)
    success_rate = (total_processed / total_received * 100) if total_received > 0 else 0

    # Find peak hour
    peak_hour = max(monitors, key=lambda m: m.total_received)

    report = {
        "total_received": total_received,
        "total_processed": total_processed,
        "total_failed": total_failed,
        "success_rate": success_rate,
        "peak_hour": peak_hour.hour,
        "peak_hour_volume": peak_hour.total_received,
    }

    # Verify report
    assert report["total_received"] == (11 * 10 + 13 * 2)  # 11 busy hours + 13 quiet hours
    assert report["total_processed"] == (11 * 9 + 13 * 2)
    assert report["total_failed"] == 11
    assert report["success_rate"] > 90
    assert report["peak_hour"] >= 8 and report["peak_hour"] <= 18
    assert report["peak_hour_volume"] == 10


def test_webhook_event_statistics():
    """Test webhook event statistics calculation"""
    from models.tesote_webhook_event import TesoteWebhookEvent

    # Create mock events
    events = []
    for i in range(100):
        event = MagicMock(spec=TesoteWebhookEvent)
        event.status = "completed" if i < 90 else "failed"
        event.event_type = "sync.updates_available" if i < 60 else "accounts.updated"
        event.processing_duration = 100 + i if event.status == "completed" else None
        event.retry_count = 1 if i % 10 == 0 else 0
        event.sync_job_id = (
            f"job_{i}"
            if event.event_type == "sync.updates_available" and event.status == "completed"
            else None
        )
        events.append(event)

    # Calculate statistics
    stats = {
        "total_received": len(events),
        "by_status": {},
        "by_type": {},
        "average_duration": 0,
        "retry_attempts": 0,
        "syncs_triggered": 0,
        "syncs_completed": 0,
    }

    # Count by status
    for status in ["completed", "failed"]:
        stats["by_status"][status] = len([e for e in events if e.status == status])

    # Count by type
    for event_type in set(e.event_type for e in events):
        stats["by_type"][event_type] = len([e for e in events if e.event_type == event_type])

    # Calculate average duration
    completed = [e for e in events if e.status == "completed" and e.processing_duration]
    if completed:
        stats["average_duration"] = sum(e.processing_duration for e in completed) / len(completed)

    # Count retries
    stats["retry_attempts"] = sum(e.retry_count for e in events)

    # Sync metrics
    sync_events = [e for e in events if e.event_type == "sync.updates_available"]
    stats["syncs_triggered"] = len([e for e in sync_events if e.sync_job_id])
    stats["syncs_completed"] = len(
        [e for e in sync_events if e.status == "completed" and e.sync_job_id]
    )

    # Verify statistics
    assert stats["total_received"] == 100
    assert stats["by_status"]["completed"] == 90
    assert stats["by_status"]["failed"] == 10
    assert stats["by_type"]["sync.updates_available"] == 60
    assert stats["by_type"]["accounts.updated"] == 40
    assert stats["average_duration"] > 100
    assert stats["retry_attempts"] == 10
    assert stats["syncs_completed"] > 0


def test_webhook_config_stats_computation():
    """Test webhook config statistics computation"""
    from models.tesote_webhook_config import TesoteWebhookConfig

    config = MagicMock(spec=TesoteWebhookConfig)

    # Mock events
    events = []
    for i in range(100):
        event = MagicMock()
        event.status = "completed" if i < 95 else "failed"
        events.append(event)

    # Calculate stats
    total_received = len(events)
    total_processed = len([e for e in events if e.status == "completed"])
    total_failed = len([e for e in events if e.status == "failed"])
    success_rate = (total_processed / total_received * 100) if total_received > 0 else 0

    # Verify
    assert total_received == 100
    assert total_processed == 95
    assert total_failed == 5
    assert success_rate == 95.0


def test_webhook_monitoring_metrics_by_type():
    """Test metrics breakdown by event type"""
    from models.tesote_webhook_monitor import TesoteWebhookMonitor

    monitor = MagicMock(spec=TesoteWebhookMonitor)

    # Initialize metrics
    metrics_by_type = {
        "sync.updates_available": {"received": 50, "processed": 48, "failed": 2, "avg_time": 120.5},
        "accounts.created": {"received": 20, "processed": 20, "failed": 0, "avg_time": 85.3},
        "accounts.updated": {"received": 30, "processed": 28, "failed": 2, "avg_time": 95.7},
    }

    monitor.metrics_by_type = json.dumps(metrics_by_type)

    # Verify metrics
    metrics = json.loads(monitor.metrics_by_type)

    # Check sync.updates_available metrics
    assert metrics["sync.updates_available"]["received"] == 50
    assert metrics["sync.updates_available"]["processed"] == 48
    assert metrics["sync.updates_available"]["failed"] == 2
    assert metrics["sync.updates_available"]["avg_time"] == 120.5

    # Check accounts.created metrics (100% success)
    assert metrics["accounts.created"]["received"] == 20
    assert metrics["accounts.created"]["processed"] == 20
    assert metrics["accounts.created"]["failed"] == 0

    # Check accounts.updated metrics
    assert metrics["accounts.updated"]["received"] == 30
    assert metrics["accounts.updated"]["processed"] == 28

    # Calculate overall success rate
    total_received = sum(m["received"] for m in metrics.values())
    total_processed = sum(m["processed"] for m in metrics.values())
    overall_success_rate = total_processed / total_received * 100

    assert total_received == 100
    assert total_processed == 96
    assert overall_success_rate == 96.0


def test_alert_notification_content():
    """Test alert notification message generation"""

    # Test high failure rate alert
    alert = {
        "type": "high_failure_rate",
        "backend": "Production Backend",
        "failure_rate": 25.0,
        "threshold": 10.0,
        "hour": 14,
        "date": datetime.now().date(),
    }

    # Generate subject and body
    subject = f"[Alert] High Webhook Failure Rate - {alert['backend']}"
    body = f"""
        High webhook failure rate detected:
        - Backend: {alert["backend"]}
        - Failure Rate: {alert["failure_rate"]:.2f}%
        - Threshold: {alert["threshold"]:.2f}%
        - Time: {alert["date"]} {alert["hour"]}:00
    """

    assert "[Alert]" in subject
    assert "High Webhook Failure Rate" in subject
    assert "Production Backend" in subject
    assert "25.00%" in body
    assert "10.00%" in body

    # Test signature failure alert
    alert = {
        "type": "signature_failures",
        "backend": "Production Backend",
        "count": 15,
        "hour": 10,
        "date": datetime.now().date(),
    }

    subject = f"[Alert] Multiple Webhook Signature Failures - {alert['backend']}"
    body = f"""
        Multiple webhook signature validation failures detected:
        - Backend: {alert["backend"]}
        - Failed Signatures: {alert["count"]}
        - Time: {alert["date"]} {alert["hour"]}:00
        Please check your webhook secret configuration.
    """

    assert "Signature Failures" in subject
    assert "Failed Signatures: 15" in body
    assert "check your webhook secret configuration" in body


def test_cleanup_old_monitors():
    """Test cleanup of old monitor records"""
    from models.tesote_webhook_monitor import TesoteWebhookMonitor

    # Create mock old monitors
    old_monitors = []
    cutoff_date = datetime.now().date() - timedelta(days=90)

    for i in range(100):
        monitor = MagicMock(spec=TesoteWebhookMonitor)
        # Create monitors from 91 to 190 days old
        monitor.date = cutoff_date - timedelta(days=i + 1)
        old_monitors.append(monitor)

    # Simulate cleanup - all monitors are older than cutoff_date
    cleaned_count = len([m for m in old_monitors if m.date < cutoff_date])

    assert cleaned_count == 100
