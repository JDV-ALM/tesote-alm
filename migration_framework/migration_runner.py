# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Migration runner - executes migrations in order, tracks schema versions
Similar to Rails rake db:migrate
"""

import importlib.util
import logging
from pathlib import Path

_logger = logging.getLogger(__name__)


class MigrationRunner:
    """
    Manages and runs database migrations

    Usage:
        runner = MigrationRunner(cr, module_path)
        runner.migrate()  # Run all pending migrations
        runner.rollback(steps=1)  # Rollback last migration
        runner.reset()  # Rollback all migrations
    """

    def __init__(self, cr, module_path):
        self.cr = cr
        self.module_path = Path(module_path)
        self.migrations_path = self.module_path / "migrations"
        self.schema_table = "tesote_schema_migrations"
        self.ensure_schema_table()

    def ensure_schema_table(self):
        """Create schema migrations tracking table (like Rails schema_migrations)"""
        self.cr.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.schema_table} (
                version VARCHAR(255) PRIMARY KEY,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                migration_name VARCHAR(255),
                direction VARCHAR(10) DEFAULT 'up'
            )
        """
        )

    def get_executed_migrations(self):
        """Get list of executed migration versions"""
        self.cr.execute(
            f"SELECT version FROM {self.schema_table} WHERE direction = 'up' ORDER BY version"
        )
        return [row[0] for row in self.cr.fetchall()]

    def get_available_migrations(self):
        """
        Scan migrations directory for migration files
        Returns list of (version, file_path, class_name) tuples
        """
        migrations = []

        if not self.migrations_path.exists():
            _logger.warning(f"Migrations directory {self.migrations_path} does not exist")
            return migrations

        # Look for migration files (format: YYYYMMDD_NNN_description.py)
        for migration_file in sorted(self.migrations_path.rglob("*.py")):
            if migration_file.name.startswith("__"):
                continue

            # Extract version from filename
            version = migration_file.stem
            if version and version[0].isdigit():
                migrations.append(
                    (version, migration_file, self._get_migration_class_name(version))
                )

        return migrations

    def _get_migration_class_name(self, version):
        """Convert version to likely class name"""
        # Remove version prefix and convert to CamelCase
        parts = version.split("_")[1:] if "_" in version else [version]
        return "".join(word.capitalize() for word in parts if word)

    def load_migration(self, file_path, class_name):
        """Load migration class from file"""
        try:
            spec = importlib.util.spec_from_file_location("migration", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Try to find migration class
            migration_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "up")
                    and hasattr(attr, "down")
                    and attr.__name__ != "BaseMigration"
                ):
                    migration_class = attr
                    break

            if not migration_class:
                raise ImportError(f"No migration class found in {file_path}")

            return migration_class(self.cr)

        except Exception as e:
            _logger.error(f"Failed to load migration {file_path}: {e}")
            raise

    def migrate(self, target_version=None):
        """
        Run all pending migrations up to target_version
        If target_version is None, run all available migrations
        """
        executed = set(self.get_executed_migrations())
        available = self.get_available_migrations()

        pending = []
        for version, file_path, class_name in available:
            if version not in executed:
                if target_version is None or version <= target_version:
                    pending.append((version, file_path, class_name))

        if not pending:
            _logger.info("No pending migrations")
            return

        _logger.info(f"Running {len(pending)} pending migrations")

        for version, file_path, class_name in pending:
            try:
                _logger.info(f"Running migration {version}")
                migration = self.load_migration(file_path, class_name)

                # Run the migration
                migration.up()

                # Optionally run seed data
                if hasattr(migration, "seed_data"):
                    migration.seed_data()

                # Record as executed
                self.record_migration(version, migration.__class__.__name__, "up")

                _logger.info(f"Migration {version} completed successfully")

            except Exception as e:
                _logger.error(f"Migration {version} failed: {e}")
                raise

    def rollback(self, steps=1):
        """
        Rollback the last N migrations
        """
        executed = self.get_executed_migrations()
        if not executed:
            _logger.info("No migrations to rollback")
            return

        # Get the last N migrations to rollback
        to_rollback = executed[-steps:] if steps <= len(executed) else executed
        to_rollback.reverse()  # Rollback in reverse order

        available = {
            version: (file_path, class_name)
            for version, file_path, class_name in self.get_available_migrations()
        }

        _logger.info(f"Rolling back {len(to_rollback)} migrations")

        for version in to_rollback:
            if version in available:
                file_path, class_name = available[version]
                try:
                    _logger.info(f"Rolling back migration {version}")
                    migration = self.load_migration(file_path, class_name)

                    # Run the rollback
                    migration.down()

                    # Remove from executed migrations
                    self.record_migration(version, migration.__class__.__name__, "down")

                    _logger.info(f"Migration {version} rolled back successfully")

                except Exception as e:
                    _logger.error(f"Rollback of migration {version} failed: {e}")
                    raise
            else:
                _logger.warning(
                    f"Migration file for {version} not found, removing from schema table"
                )
                self.remove_migration_record(version)

    def reset(self):
        """Rollback all migrations"""
        executed = self.get_executed_migrations()
        if executed:
            self.rollback(len(executed))

    def status(self):
        """Show migration status (like Rails rake db:migrate:status)"""
        executed = set(self.get_executed_migrations())
        available = self.get_available_migrations()

        print("\n" + "=" * 60)
        print("MIGRATION STATUS")
        print("=" * 60)

        if not available:
            print("No migrations found")
            return

        print(f"{'Status':<10} {'Version':<20} {'Migration'}")
        print("-" * 60)

        for version, file_path, class_name in available:
            status = "up" if version in executed else "down"
            print(f"{status:<10} {version:<20} {class_name}")

        print("-" * 60)
        print(
            f"Total: {len(available)}, Executed: {len(executed)}, Pending: {len(available) - len(executed)}"
        )
        print()

    def record_migration(self, version, migration_name, direction):
        """Record migration execution in schema table"""
        if direction == "up":
            self.cr.execute(
                f"""
                INSERT INTO {self.schema_table} (version, migration_name, direction)
                VALUES (%s, %s, %s)
                ON CONFLICT (version) DO UPDATE SET
                    executed_at = CURRENT_TIMESTAMP,
                    direction = %s
            """,
                (version, migration_name, direction, direction),
            )
        else:  # down
            self.cr.execute(f"DELETE FROM {self.schema_table} WHERE version = %s", (version,))

    def remove_migration_record(self, version):
        """Remove migration record (for cleanup)"""
        self.cr.execute(f"DELETE FROM {self.schema_table} WHERE version = %s", (version,))

    def create_migration(self, name):
        """
        Generate a new migration file (like Rails rails generate migration)

        Usage:
            runner.create_migration("CreateWebhookTables")
            runner.create_migration("AddIndexToTransactions")
        """
        from datetime import datetime

        # Generate version timestamp
        version = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Convert name to snake_case for filename
        snake_name = "".join(
            ["_" + c.lower() if c.isupper() and i > 0 else c.lower() for i, c in enumerate(name)]
        ).lstrip("_")

        filename = f"{version}_{snake_name}.py"
        file_path = self.migrations_path / filename

        # Ensure migrations directory exists
        self.migrations_path.mkdir(parents=True, exist_ok=True)

        # Generate migration template
        template = f'''# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Migration: {name}
Generated: {datetime.now().isoformat()}
"""

from ..migration_framework import BaseMigration


class {name}(BaseMigration):
    version = "{version}"
    description = "{name}"

    def up(self):
        """Run the migration"""
        # Example:
        # self.create_table('my_table', [
        #     ('id', 'SERIAL PRIMARY KEY'),
        #     ('name', 'VARCHAR(255) NOT NULL'),
        #     ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        # ])
        pass

    def down(self):
        """Rollback the migration"""
        # Example:
        # self.drop_table('my_table')
        pass

    def seed_data(self):
        """Optional: Add seed data"""
        # Example:
        # self.insert_data('my_table', [
        #     {{'name': 'Test Record'}},
        # ])
        pass
'''

        with open(file_path, "w") as f:
            f.write(template)

        _logger.info(f"Created migration: {file_path}")
        print(f"Created migration: {filename}")

        return file_path
