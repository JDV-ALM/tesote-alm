# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Main migration entry point - called by Odoo during module installation/upgrade
"""

import logging
from .management_commands import MigrationCommands

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Main migration entry point called by Odoo
    This replaces the traditional pre-migration.py and post-migration.py files
    """
    _logger.info(f"Starting tesote_connector migrations to version {version}")
    
    try:
        # Run all pending migrations
        MigrationCommands.migrate(cr)
        
        # Show final status
        _logger.info("Migration status:")
        MigrationCommands.status(cr)
        
        _logger.info(f"Completed tesote_connector migrations to version {version}")
        
    except Exception as e:
        _logger.error(f"Migration failed: {e}")
        raise