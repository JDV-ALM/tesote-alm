# tesote.com Odoo API Connector

Odoo 18.0 connector for **tesote.com API v2.0.0** - Real-time financial data synchronization.

## Features

- **Client to tesote.com Sync**: Real-time transaction synchronization using v2 `/transactions/sync` endpoint
- **Cursor-Based Sync**: Efficient incremental updates with cursor management
- **Transaction Lifecycle**: Handles pending → completed state transitions
- **Webhook Ready**: Support for webhook notifications
- **Multi-Company**: Support for multiple companies and backends

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

1. Go to **Connectors → tesote.com → Backends**
2. Create a new backend with:
   - API URL: `https://staging.tesote.com`
   - API Token: Your bearer token
   - Webhook URL/Secret (optional): For webhook notifications

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
# With Docker
./bin/docker-dev test

# Without Docker
./bin/test                          # Run all tests
./bin/test --module tesote_connector  # Test specific module
```


### Additional Tools
- **pgAdmin**: http://localhost:5050 (admin@tesote.com / admin)
- **API Docs**: https://equipo.tesote.com/api/docs?version=v2

## API Endpoints Used

- `GET /api/v2/accounts` - Fetch accounts
- `GET /api/v2/accounts/{id}` - Fetch single account
- `POST /api/v2/transactions/sync` - Sync transactions (cursor-based)
- `GET /api/v2/status` - Check API status
- `GET /api/v2/whoami` - Get client information

## License

LGPL-3.0 or later

## Support

For tesote.com API documentation: https://equipo.tesote.com/api/docs?version=v2
For issues: https://github.com/tesote/tesote-odoo-api-connector/issues