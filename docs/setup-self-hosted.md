# Installing Tesote Connector on Existing Odoo Server

This guide shows how to install the Tesote Connector module on an existing, working Odoo server.

## Prerequisites

- Working Odoo 18 server with database access
- SSH/terminal access to your server
- Git installed (or ability to install it)

## Step 1: Access Your Server

Connect to your Odoo server via SSH:

```bash
ssh your-user@your-server-ip
```

## Step 2: Locate Your Addons Directory

Find where your custom addons are stored. Common locations:

```bash
# Check your current Odoo config
cat /etc/odoo/odoo.conf | grep addons_path

# Common addon directories:
ls /opt/odoo/addons/          # Custom installation
ls /var/lib/odoo/addons/      # Package installation
ls /usr/lib/python3/dist-packages/odoo/addons/  # System installation
```

If you don't have a custom addons directory, create one:

```bash
sudo mkdir -p /opt/odoo/custom-addons
sudo chown odoo:odoo /opt/odoo/custom-addons
```

## Step 3: Update Odoo Configuration

Edit your Odoo config file to include the custom addons path:

```bash
sudo nano /etc/odoo/odoo.conf
```

Add or update the addons_path line:

```ini
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/opt/odoo/custom-addons
```

## Step 4: Download the Tesote Connector

Navigate to your custom addons directory:

```bash
cd /opt/odoo/custom-addons
```

Install git if not available:

```bash
sudo apt update && sudo apt install -y git
```

Clone the module:

```bash
sudo git clone https://github.com/tesote/tesote-odoo-api-connector.git tesote_connector
```

Set proper permissions:

```bash
sudo chown -R odoo:odoo tesote_connector
```

## Step 5: Install the Module

### Method 1: Command Line Installation

Stop your Odoo service:

```bash
sudo systemctl stop odoo
```

Install the module:

```bash
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d your_database_name -i tesote_connector --stop-after-init
```

Start Odoo service:

```bash
sudo systemctl start odoo
```

### Method 2: Web Interface Installation

1. Restart your Odoo service:
   ```bash
   sudo systemctl restart odoo
   ```

2. Login to your Odoo web interface

3. Go to **Apps** → **Update Apps List**

4. Search for "tesote_connector"

5. Click **Install**

## Step 6: Verify Installation

Check that the module is installed:

1. Go to **Apps** → **Installed Apps**
2. Search for "tesote_connector"
3. The module should appear in the list

Or check via command line:

```bash
sudo -u odoo odoo shell -c /etc/odoo/odoo.conf -d your_database_name
```

```python
installed_modules = env['ir.module.module'].search([('state', '=', 'installed'), ('name', '=', 'tesote_connector')])
print("Module installed:" if installed_modules else "Module not found")
exit()
```

## Troubleshooting

### Module Not Appearing in Apps

If the module doesn't appear:

1. Check file permissions:
   ```bash
   ls -la /opt/odoo/custom-addons/tesote_connector/
   sudo chown -R odoo:odoo /opt/odoo/custom-addons/tesote_connector/
   ```

2. Verify the manifest file exists:
   ```bash
   cat /opt/odoo/custom-addons/tesote_connector/__manifest__.py
   ```

3. Check addons_path in config:
   ```bash
   cat /etc/odoo/odoo.conf | grep addons_path
   ```

4. Restart Odoo and update apps list again

### Module Installation Fails

If installation fails:

1. Check Odoo logs:
   ```bash
   sudo tail -f /var/log/odoo/odoo.log
   ```

2. Verify database connection:
   ```bash
   sudo -u odoo psql -d your_database_name -c "SELECT 1;"
   ```

3. Try installing with verbose logging:
   ```bash
   sudo -u odoo odoo -c /etc/odoo/odoo.conf -d your_database_name -i tesote_connector --log-level=debug --stop-after-init
   ```

### Service Won't Start

If Odoo won't start after changes:

1. Check service status:
   ```bash
   sudo systemctl status odoo
   ```

2. Check configuration file syntax:
   ```bash
   sudo -u odoo odoo -c /etc/odoo/odoo.conf --test-enable
   ```

3. Revert addons_path if needed and restart:
   ```bash
   sudo systemctl start odoo
   ```

## Multiple Database Setup

If you have multiple databases, install on specific database:

```bash
# Install on specific database
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d database1 -i tesote_connector --stop-after-init
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d database2 -i tesote_connector --stop-after-init
```

## Production Considerations

- **Backup first**: Always backup your database before installing new modules
- **Test environment**: Test the module on a staging server first
- **Scheduled downtime**: Plan for brief downtime during installation
- **Monitor logs**: Watch logs during and after installation

## Uninstalling (if needed)

To remove the module:

```bash
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d your_database_name -u tesote_connector --stop-after-init
```

Or via web interface: **Apps** → **Installed Apps** → Find module → **Uninstall**

## Next Steps

After successful installation:

1. Configure the module settings
2. Set up API connections
3. Test functionality
4. Monitor performance

The module is now ready for configuration and use!
