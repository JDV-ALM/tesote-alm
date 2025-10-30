# tesote.com Odoo API Connector

Odoo 18.0 connector for **tesote.com API v2.0.0** - Real-time financial data synchronization.

## Recent Updates

**Latest Fixes (January 2025)**:
- Fixed account balance field mapping - now correctly reads `balance_cents`/`available_balance_cents` from API and converts to dollars
- Updated to use RESTful nested sync endpoint: `POST /api/v2/accounts/{id}/transactions/sync` (recommended structure)
- Added `balance_data_current_as_of` timestamp field for balance data tracking
- All 112 tests passing with full API v2.0.0 specification compliance

## Features

- **RESTful Transaction Sync**: Real-time transaction synchronization using v2 nested endpoint `/accounts/{id}/transactions/sync`
- **Accurate Balance Tracking**: Proper conversion from cents to dollars with timestamp tracking
- **Cursor-Based Sync**: Efficient incremental updates with cursor management
- **Transaction Lifecycle**: Handles pending → completed state transitions (36 business hours)
- **Real-time Webhooks**: Secure HMAC-SHA256 verified webhook processing with event subscriptions
- **Multi-Company**: Support for multiple companies and backends
- **Singleton Backend**: Single configuration pattern for simplified management

## Requirements

- Odoo 18.0
- Python packages: `requests`
- Docker and Docker Compose (for local development)

## Compatibility

**Currently supported deployment methods:**
- **Self-hosted Odoo** - Full support for on-premise installations
- **Odoo.sh** - Compatible with Odoo.sh cloud platform

> **Note**: This module currently works only with self-hosted Odoo installations or Odoo.sh deployments. Support for Odoo Online (SaaS) is not yet available.

## Quick Start with Docker

### 1. Start the Docker environment
```bash
./bin/docker-dev up
```

### 2. Access Odoo
- URL: http://localhost:8069
- Username: admin
- Password: admin
- Database: tesote_dev

### 3. Install the module
```bash
./bin/docker-dev install
```

Or manually through Odoo:
1. Go to Apps → Update Apps List
2. Search for "tesote.com Connector"
3. Click Install

## Installation on Self-Hosted Odoo

### Prerequisites
1. Access to your Odoo server with admin privileges
2. Ability to add custom modules to your addons path
3. Python dependencies management access

### Installation Steps

1. **Clone or download this repository** to your server:
```bash
git clone https://github.com/tesote/tesote-odoo-api-connector.git
cd tesote-odoo-api-connector
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Copy the module** to your Odoo addons directory:
```bash
# Example for typical Odoo installation
cp -r tesote_connector /opt/odoo/addons/
# Or add to your custom addons path
cp -r tesote_connector /path/to/your/custom-addons/
```

4. **Update Odoo configuration** to include the addons path (if using custom path):
```ini
# In your odoo.conf file
addons_path = /opt/odoo/addons,/path/to/your/custom-addons
```

5. **Restart Odoo service**:
```bash
sudo systemctl restart odoo
# Or if using custom service name
sudo systemctl restart odoo18
```

6. **Install the module** in Odoo:
   - Login to Odoo with administrator account
   - Go to **Apps** menu
   - Click **Update Apps List**
   - Search for "tesote.com Connector"
   - Click **Install**

### Installation on Odoo.sh

1. **Add the module** to your project repository:
   - Add `tesote_connector` folder to your project's addons directory
   - Commit and push to your Odoo.sh repository

2. **Install dependencies**:
   - Add `requests` to your `requirements.txt` file in the project root
   - Commit and push the changes

3. **Deploy and install**:
   - Deploy changes to your Odoo.sh branch
   - Go to Apps → Update Apps List
   - Search and install "tesote.com Connector"

## Configuration

### Backend Setup
1. Go to **Connectors → tesote.com → Backends**
2. Create a new backend with:
   - API URL: `https://staging.tesote.com`
   - API Token: Your bearer token

### Webhook Configuration (Optional)
3. Go to **Connectors → tesote.com → Webhook Configuration**
4. Configure webhook settings:
   - **Enable webhooks** - Toggle webhook processing
   - **Event subscriptions** - Choose which events to receive:
     - `sync.updates_available` - Triggers automatic sync when new data is available
     - `accounts.created` - Notifies when new accounts are added
     - `accounts.updated` - Notifies when account details change
     - `transactions.created` - Real-time transaction notifications (optional)
     - `transactions.updated` - Transaction status updates (optional)
   - **Security** - Automatic HMAC-SHA256 signature verification
   - **Monitoring** - Built-in webhook event tracking and failure alerts

5. **Webhook URL**: Your endpoint will be automatically generated as:
   ```
   https://your-odoo-domain.com/tesote/webhook
   ```

6. **Configure in tesote.com**:
   - Use the generated webhook URL in your tesote.com API settings
   - Copy the secret key from the configuration (click "Show Secret")
   - Subscribe to the events you've enabled in Odoo

## Usage

### Import Accounts
Navigate to backend and click "Import Accounts"

### Sync Transactions
Use the "Sync Transactions" button or set up scheduled actions

### API Methods

```python
# Get backend
backend = env['tesote.backend'].search([('name', '=', 'Production')])

# Sync all transactions
backend.sync_transactions_v2()

# Sync specific account
account = env['tesote.account'].search([('tesote_id', '=', 'account-uuid')])
account.import_transactions()
```

## Development

### Quick Setup
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --dev

# Install pre-commit hooks
source .venv/bin/activate && pre-commit install

# Run tests
uv run pytest

# Run linters
uv run ruff check --fix .
uv run black .
uv run isort .
```

### Docker Commands
```bash
./bin/docker-dev up          # Start environment
./bin/docker-dev down        # Stop environment
./bin/docker-dev logs odoo   # View logs
./bin/docker-dev test        # Run tests
./bin/docker-dev shell       # Open Odoo Python shell
./bin/docker-dev backup      # Create database backup
./bin/docker-dev status      # Check environment status
```


### Testing
```bash
# Run all 112 tests
uv run pytest

# Run with coverage report
uv run pytest --cov=. --cov-report=term-missing

# Run specific test categories
uv run pytest tests/test_adapter*.py -v      # API communication tests
uv run pytest tests/test_webhook*.py -v      # Webhook tests
uv run pytest tests/test_phase4_security.py -v  # Security tests
```

All tests can run without Odoo installation thanks to mock infrastructure in `tests/conftest.py`.

### Additional Tools
- **pgAdmin**: http://localhost:5050 (admin@tesote.com / admin)
- **API Docs**: https://equipo.tesote.com/api/docs?version=v2

## API Endpoints Used

- `GET /api/v2/accounts` - Fetch accounts list
- `GET /api/v2/accounts/{id}` - Fetch single account details
- `POST /api/v2/accounts/{id}/transactions/sync` - Sync transactions for specific account (cursor-based, RESTful nested endpoint)
- `GET /api/v2/status` - Check API status
- `GET /api/v2/whoami` - Get client information

**Note**: Uses the recommended RESTful nested sync endpoint structure with account ID in the URL path.

## Data Mapping

### Account Fields
| tesote.com API Field       | Odoo Field                 | Notes                           |
|----------------------------|----------------------------|---------------------------------|
| `balance_cents`            | `balance`                  | Converted from cents to dollars |
| `available_balance_cents`  | `balance` (fallback)       | Used if balance_cents not set   |
| `balance_data_current_as_of` | `balance_data_current_as_of` | ISO timestamp of balance data |
| `id`                       | `tesote_id`                | Unique account identifier       |
| `name`                     | `name`                     | Account display name            |

### Transaction Fields
| tesote.com API Field | Odoo Field          | Notes                          |
|----------------------|---------------------|--------------------------------|
| `amount`             | `amount`            | Already in dollars             |
| `transaction_id`     | `tesote_id`         | Unique transaction identifier  |
| `pending`            | `status`            | Maps to pending/completed      |
| `merchant_name`      | `counterparty_name` | Transaction counterparty       |
| `date`               | `date`              | ISO timestamp converted to UTC |

## Webhook Events Supported

- `sync.updates_available` - Triggered when new transactions are available for sync
- `accounts.created` - New account created in tesote.com
- `accounts.updated` - Account details updated (balance, name, etc.)
- `transactions.created` - New transaction added (real-time)
- `transactions.updated` - Transaction status changed (pending → completed)

## License

LGPL-3.0 or later

## Support

For tesote.com API documentation: https://equipo.tesote.com/api/docs?version=v2
For issues: https://github.com/tesote/tesote-odoo-api-connector/issues
