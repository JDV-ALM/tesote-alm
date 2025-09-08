# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

{
    "name": "tesote.com Connector",
    "version": "18.0.1.0.0",
    "author": "tesote.com",
    "maintainer": "tesote.com",
    "website": "https://github.com/tesote/tesote-odoo-api-connector",
    "license": "LGPL-3",
    "category": "Accounting/Accounting",
    "summary": "Real-time synchronization of financial data from tesote.com API v2 with Odoo - Accounts, transactions, and automated reconciliation",
    "description": """
tesote.com Connector for Odoo
==============================

Seamlessly integrate your tesote.com financial data with Odoo 18.0.

Key Features:
-------------
* **Real-time Sync**: Automatic synchronization of accounts and transactions
* **Cursor-Based Updates**: Efficient incremental data updates
* **Transaction Lifecycle**: Handles pending to completed state transitions
* **Multi-language**: Full support for English and Spanish
* **Rate Limiting**: Built-in support for Standard/Premium/Enterprise tiers
* **Webhook Ready**: Real-time notifications support
* **Single Backend**: Singleton pattern ensures single configuration

Technical Highlights:
--------------------
* Uses tesote.com API v2.0.0
* Cursor-based incremental synchronization
* Automatic handling of transaction states
* Full internationalization (i18n) support
* Comprehensive error handling and logging
    """,
    "depends": [
        "account",
        "base",
    ],
    "external_dependencies": {
        "python": [
            "requests"
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "views/tesote_backend_views.xml",
        "views/tesote_account_views.xml",
        "views/tesote_transaction_views.xml",
        "views/tesote_menu.xml",
    ],
    "images": [
        "static/description/banner.png",
        "static/description/screenshot_1.png",
        "static/description/screenshot_2.png",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "development_status": "Beta",
    "support": "support-odoo@tesote.com",
}