#!/usr/bin/env python3
"""
Webhook Testing Tool for Tesote-Odoo API Connector.

This tool allows you to:
- Simulate webhook calls from tesote.com
- Generate valid HMAC-SHA256 signatures
- Test different event types
- Verify webhook processing
- Test error scenarios

Usage:
    python webhook_tester.py --url http://localhost:8069/tesote/webhook \
        --secret your_secret_key --event sync.updates_available
    python webhook_tester.py --url http://localhost:8069/tesote/webhook \
        --secret your_secret_key --event accounts.created --account-id acc_123
    python webhook_tester.py --url http://localhost:8069/tesote/webhook --secret your_secret_key --batch 10
"""

import argparse
import json
import hmac
import hashlib
import time
import uuid
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import random


class WebhookTester:
    """Webhook testing utility."""

    def __init__(self, webhook_url: str, secret_key: str, verbose: bool = False):
        """Initialize webhook tester.

        Args:
            webhook_url: The webhook endpoint URL
            secret_key: The secret key for signature generation
            verbose: Enable verbose output
        """
        self.webhook_url = webhook_url
        self.secret_key = secret_key
        self.verbose = verbose

    def generate_signature(self, payload: Dict[str, Any], timestamp: str) -> str:
        """Generate HMAC-SHA256 signature.

        Args:
            payload: The webhook payload
            timestamp: Unix timestamp as string

        Returns:
            Formatted signature string
        """
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            self.secret_key.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    def generate_event_id(self) -> str:
        """Generate a unique webhook event ID."""
        return f"whd_{uuid.uuid4().hex[:12]}"

    def create_sync_updates_payload(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a sync.updates_available webhook payload.

        Args:
            account_id: Optional account ID to use

        Returns:
            Webhook payload dictionary
        """
        account_id = account_id or f"acc_{uuid.uuid4().hex[:8]}"

        # Generate random transaction IDs
        new_ids = [f"tr_new_{uuid.uuid4().hex[:8]}" for _ in range(random.randint(1, 5))]
        updated_ids = [f"tr_upd_{uuid.uuid4().hex[:8]}" for _ in range(random.randint(0, 3))]
        removed_ids = [f"tr_del_{uuid.uuid4().hex[:8]}" for _ in range(random.randint(0, 2))]

        return {
            "id": self.generate_event_id(),
            "event": "sync.updates_available",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": account_id,
                "new_ids": new_ids,
                "updated_ids": updated_ids,
                "removed_ids": removed_ids,
                "new_transactions": len(new_ids),
                "modified_transactions": len(updated_ids),
                "removed_transactions": len(removed_ids),
                "api_sync_cursor": {
                    "sync_from": "2023-08-20T10:30:00Z",
                    "sync_to": datetime.now(timezone.utc).isoformat()
                }
            }
        }

    def create_account_created_payload(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Create an accounts.created webhook payload.

        Args:
            account_id: Optional account ID to use

        Returns:
            Webhook payload dictionary
        """
        account_id = account_id or f"acc_{uuid.uuid4().hex[:8]}"

        return {
            "id": self.generate_event_id(),
            "event": "accounts.created",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": account_id,
                "institution_id": f"ins_{uuid.uuid4().hex[:8]}",
                "name": f"Test Account {random.randint(1000, 9999)}",
                "currency": random.choice(["USD", "EUR", "GBP", "MXN"]),
                "balance": round(random.uniform(100, 10000), 2),
                "type": random.choice(["depository", "credit", "investment"]),
                "subtype": random.choice(["checking", "savings", "credit_card"])
            }
        }

    def create_account_updated_payload(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Create an accounts.updated webhook payload.

        Args:
            account_id: Optional account ID to use

        Returns:
            Webhook payload dictionary
        """
        account_id = account_id or f"acc_{uuid.uuid4().hex[:8]}"

        return {
            "id": self.generate_event_id(),
            "event": "accounts.updated",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": account_id,
                "balance": round(random.uniform(100, 10000), 2),
                "updated_fields": ["balance", "name"],
                "name": f"Updated Account {random.randint(1000, 9999)}"
            }
        }

    def create_transaction_state_changed_payload(self, transaction_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a transactions.state_changed webhook payload.

        Args:
            transaction_id: Optional transaction ID to use

        Returns:
            Webhook payload dictionary
        """
        transaction_id = transaction_id or f"tr_{uuid.uuid4().hex[:8]}"

        return {
            "id": self.generate_event_id(),
            "event": "transactions.state_changed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": transaction_id,
                "previous_state": "pending",
                "state": "completed",
                "account_id": f"acc_{uuid.uuid4().hex[:8]}",
                "amount": round(random.uniform(10, 1000), 2),
                "aged_at": datetime.now(timezone.utc).isoformat()
            }
        }

    def send_webhook(self, payload: Dict[str, Any],
                     invalid_signature: bool = False,
                     missing_headers: bool = False,
                     timeout: Optional[int] = None) -> requests.Response:
        """Send a webhook request.

        Args:
            payload: The webhook payload
            invalid_signature: Whether to send an invalid signature
            missing_headers: Whether to omit required headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        timestamp = str(int(time.time()))

        # Generate signature (valid or invalid)
        if invalid_signature:
            signature = f"t={timestamp},v1=invalid_signature_12345"
        else:
            signature = self.generate_signature(payload, timestamp)

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Tesote-Webhook-Tester/1.0'
        }

        if not missing_headers:
            headers['X-Tesote-Webhook-Signature'] = signature
            headers['X-Tesote-Webhook-Id'] = payload.get('id', 'test_webhook')

        # Prepare request
        if self.verbose:
            print("\n" + "=" * 60)
            print(f"Sending webhook to: {self.webhook_url}")
            print(f"Event type: {payload.get('event', 'unknown')}")
            print(f"Event ID: {payload.get('id', 'unknown')}")
            print(f"Timestamp: {timestamp}")
            print(f"Signature: {signature[:50]}..." if len(signature) > 50 else signature)
            print("\nPayload:")
            print(json.dumps(payload, indent=2))
            print("=" * 60 + "\n")

        # Send request
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=timeout or 10
            )

            if self.verbose:
                print(f"Response Status: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                try:
                    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
                except (ValueError, json.JSONDecodeError):
                    print(f"Response Body: {response.text}")

            return response

        except requests.RequestException as e:
            if self.verbose:
                print(f"Request failed: {e}")
            raise

    def test_event_type(self, event_type: str, account_id: Optional[str] = None) -> bool:
        """Test a specific webhook event type.

        Args:
            event_type: The event type to test
            account_id: Optional account ID

        Returns:
            True if successful, False otherwise
        """
        # Create payload based on event type
        if event_type == 'sync.updates_available':
            payload = self.create_sync_updates_payload(account_id)
        elif event_type == 'accounts.created':
            payload = self.create_account_created_payload(account_id)
        elif event_type == 'accounts.updated':
            payload = self.create_account_updated_payload(account_id)
        elif event_type == 'transactions.state_changed':
            payload = self.create_transaction_state_changed_payload()
        else:
            print(f"Unknown event type: {event_type}")
            return False

        # Send webhook
        try:
            response = self.send_webhook(payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def test_error_scenarios(self) -> Dict[str, bool]:
        """Test various error scenarios.

        Returns:
            Dictionary of test results
        """
        results = {}

        # Test invalid signature
        print("\nTesting invalid signature...")
        payload = self.create_sync_updates_payload()
        try:
            response = self.send_webhook(payload, invalid_signature=True)
            results['invalid_signature'] = response.status_code == 401
            print(f"  Result: {'PASS' if results['invalid_signature'] else 'FAIL'} (Status: {response.status_code})")
        except Exception:
            results['invalid_signature'] = False
            print("  Result: FAIL (Exception)")

        # Test missing headers
        print("\nTesting missing headers...")
        payload = self.create_sync_updates_payload()
        try:
            response = self.send_webhook(payload, missing_headers=True)
            results['missing_headers'] = response.status_code in [400, 401]
            print(f"  Result: {'PASS' if results['missing_headers'] else 'FAIL'} (Status: {response.status_code})")
        except Exception:
            results['missing_headers'] = False
            print("  Result: FAIL (Exception)")

        # Test malformed JSON
        print("\nTesting malformed payload...")
        try:
            response = requests.post(
                self.webhook_url,
                data='{"invalid": json}',
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            results['malformed_json'] = response.status_code == 400
            print(f"  Result: {'PASS' if results['malformed_json'] else 'FAIL'} (Status: {response.status_code})")
        except Exception:
            results['malformed_json'] = False
            print("  Result: FAIL (Exception)")

        # Test duplicate webhook (send same webhook twice)
        print("\nTesting idempotency (duplicate webhook)...")
        payload = self.create_sync_updates_payload()
        try:
            response1 = self.send_webhook(payload)
            time.sleep(1)  # Small delay
            response2 = self.send_webhook(payload)
            results['idempotency'] = (response1.status_code == 200 and response2.status_code == 200)
            status_msg = f"(Status: {response1.status_code}, {response2.status_code})"
            print(f"  Result: {'PASS' if results['idempotency'] else 'FAIL'} {status_msg}")
        except Exception:
            results['idempotency'] = False
            print("  Result: FAIL (Exception)")

        return results

    def send_batch(self, count: int, delay: float = 0.5) -> Dict[str, Any]:
        """Send a batch of webhook events.

        Args:
            count: Number of webhooks to send
            delay: Delay between webhooks in seconds

        Returns:
            Summary of results
        """
        results = {
            'total': count,
            'successful': 0,
            'failed': 0,
            'events': []
        }

        print(f"\nSending batch of {count} webhooks...")

        for i in range(count):
            # Randomly select event type
            event_types = [
                'sync.updates_available',
                'accounts.created',
                'accounts.updated',
                'transactions.state_changed'
            ]
            event_type = random.choice(event_types)

            # Create and send webhook
            if event_type == 'sync.updates_available':
                payload = self.create_sync_updates_payload()
            elif event_type == 'accounts.created':
                payload = self.create_account_created_payload()
            elif event_type == 'accounts.updated':
                payload = self.create_account_updated_payload()
            else:
                payload = self.create_transaction_state_changed_payload()

            try:
                response = self.send_webhook(payload)
                if response.status_code == 200:
                    results['successful'] += 1
                    status = 'SUCCESS'
                else:
                    results['failed'] += 1
                    status = 'FAILED'

                results['events'].append({
                    'event_id': payload['id'],
                    'event_type': event_type,
                    'status': status,
                    'status_code': response.status_code
                })

                print(f"  [{i+1}/{count}] {event_type}: {status} ({response.status_code})")

            except Exception as e:
                results['failed'] += 1
                results['events'].append({
                    'event_id': payload['id'],
                    'event_type': event_type,
                    'status': 'ERROR',
                    'error': str(e)
                })
                print(f"  [{i+1}/{count}] {event_type}: ERROR ({e})")

            if i < count - 1:
                time.sleep(delay)

        # Print summary
        print("\nBatch complete:")
        print(f"  Total: {results['total']}")
        print(f"  Successful: {results['successful']} ({results['successful']/count*100:.1f}%)")
        print(f"  Failed: {results['failed']} ({results['failed']/count*100:.1f}%)")

        return results

    def verify_processing(self, event_id: str, api_url: str, api_key: str) -> bool:
        """Verify that a webhook was processed by checking the API.

        Args:
            event_id: The webhook event ID
            api_url: The API URL to check
            api_key: The API key for authentication

        Returns:
            True if processed, False otherwise
        """
        # This would typically check the actual system to verify processing
        # For testing, we'll just make a simple API call
        try:
            response = requests.get(
                f"{api_url}/webhook/events/{event_id}",
                headers={'X-API-Key': api_key},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False


def main():
    """Main entry point for webhook tester."""
    parser = argparse.ArgumentParser(description='Tesote Webhook Testing Tool')
    parser.add_argument('--url', required=True, help='Webhook endpoint URL')
    parser.add_argument('--secret', required=True, help='Webhook secret key')
    parser.add_argument('--event', help='Event type to test')
    parser.add_argument('--account-id', help='Account ID to use in payload')
    parser.add_argument('--transaction-id', help='Transaction ID to use in payload')
    parser.add_argument('--batch', type=int, help='Send batch of N webhooks')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between batch webhooks (seconds)')
    parser.add_argument('--test-errors', action='store_true', help='Test error scenarios')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--invalid-signature', action='store_true', help='Send invalid signature')
    parser.add_argument('--missing-headers', action='store_true', help='Omit required headers')

    args = parser.parse_args()

    # Create tester
    tester = WebhookTester(args.url, args.secret, args.verbose)

    # Run appropriate test
    if args.test_errors:
        print("Testing error scenarios...")
        results = tester.test_error_scenarios()
        print("\nError scenario results:")
        for test, passed in results.items():
            print(f"  {test}: {'PASS' if passed else 'FAIL'}")

    elif args.batch:
        results = tester.send_batch(args.batch, args.delay)

    elif args.event:
        print(f"Testing {args.event} event...")
        success = tester.test_event_type(args.event, args.account_id)
        print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")

    else:
        # Default: send a single sync.updates_available webhook
        payload = tester.create_sync_updates_payload(args.account_id)

        # Apply test modifiers
        response = tester.send_webhook(
            payload,
            invalid_signature=args.invalid_signature,
            missing_headers=args.missing_headers
        )

        print(f"\nResult: {'SUCCESS' if response.status_code == 200 else 'FAILED'}")


if __name__ == '__main__':
    main()
