# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

# Only import when running in Odoo context
# Tests will mock these modules
try:
    from . import models
    from . import components
    from . import controllers
except ImportError:
    # Running in test environment
    pass


def post_init_hook(cr, registry):
    """
    Post-initialization hook to run database migrations
    This runs after the module is installed/upgraded
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    _logger.info("Running tesote_connector post-initialization")
    
    try:
        # Import here to avoid circular imports
        from .migrations.migrate import migrate as run_migrations
        
        # Run database migrations
        run_migrations(cr, registry.version)
        _logger.info("Database migrations completed successfully")
    except Exception as e:
        _logger.error(f"Migration failed during post_init_hook: {e}")
        # Don't re-raise to avoid blocking module installation
        # Users can run migrations manually if needed