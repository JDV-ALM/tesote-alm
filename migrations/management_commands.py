# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Management commands for database migrations
Similar to Rails rake db: commands
"""

import logging
from pathlib import Path
from ..migration_framework import MigrationRunner

_logger = logging.getLogger(__name__)


class MigrationCommands:
    """
    Provides Rails-like migration commands
    
    Usage in Odoo shell:
        from odoo.addons.tesote_connector.migrations.management_commands import MigrationCommands
        
        # Run migrations
        MigrationCommands.migrate(env.cr)
        
        # Check status
        MigrationCommands.status(env.cr)
        
        # Rollback
        MigrationCommands.rollback(env.cr, steps=1)
        
        # Create new migration
        MigrationCommands.generate(env.cr, "AddIndexToTransactions")
    """
    
    @staticmethod
    def get_runner(cr):
        """Get migration runner instance"""
        module_path = Path(__file__).parent.parent
        return MigrationRunner(cr, module_path)
    
    @classmethod
    def migrate(cls, cr, target_version=None):
        """Run all pending migrations (like rake db:migrate)"""
        runner = cls.get_runner(cr)
        runner.migrate(target_version)
        cr.commit()
        print("✅ Migrations completed successfully")
    
    @classmethod
    def rollback(cls, cr, steps=1):
        """Rollback migrations (like rake db:rollback)"""
        runner = cls.get_runner(cr)
        runner.rollback(steps)
        cr.commit()
        print(f"✅ Rolled back {steps} migration(s)")
    
    @classmethod
    def reset(cls, cr):
        """Rollback all migrations (like rake db:reset)"""
        runner = cls.get_runner(cr)
        runner.reset()
        cr.commit()
        print("✅ All migrations rolled back")
    
    @classmethod
    def status(cls, cr):
        """Show migration status (like rake db:migrate:status)"""
        runner = cls.get_runner(cr)
        runner.status()
    
    @classmethod
    def generate(cls, cr, name):
        """Generate new migration file (like rails generate migration)"""
        runner = cls.get_runner(cr)
        file_path = runner.create_migration(name)
        print(f"✅ Created migration: {file_path}")
        return file_path
    
    @classmethod 
    def seed(cls, cr):
        """Run seed data for all migrations"""
        runner = cls.get_runner(cr)
        migrations = runner.get_available_migrations()
        
        for version, file_path, class_name in migrations:
            try:
                migration = runner.load_migration(file_path, class_name)
                if hasattr(migration, 'seed_data'):
                    migration.seed_data()
                    print(f"✅ Seeded data for {version}")
            except Exception as e:
                print(f"❌ Seed failed for {version}: {e}")
        
        cr.commit()
        print("✅ Seed data completed")


# Convenience functions for direct use
def migrate(cr, target_version=None):
    """Run migrations"""
    return MigrationCommands.migrate(cr, target_version)

def rollback(cr, steps=1):
    """Rollback migrations"""
    return MigrationCommands.rollback(cr, steps)

def status(cr):
    """Show migration status"""
    return MigrationCommands.status(cr)

def generate(cr, name):
    """Generate new migration"""
    return MigrationCommands.generate(cr, name)

def seed(cr):
    """Run seed data"""
    return MigrationCommands.seed(cr)