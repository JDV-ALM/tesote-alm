# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Rails-like migration framework for Odoo
Provides similar functionality to Rails ActiveRecord migrations
"""

import logging
from datetime import datetime
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


class BaseMigration(ABC):
    """
    Base class for database migrations, similar to Rails ActiveRecord::Migration
    
    Usage:
        class CreateWebhookTables(BaseMigration):
            version = "20241201_001"
            
            def up(self):
                self.create_table('tesote_webhook_config', [
                    ('id', 'SERIAL PRIMARY KEY'),
                    ('backend_id', 'INTEGER REFERENCES tesote_backend(id)'),
                    ('webhook_url', 'VARCHAR(255)'),
                    ('secret_key', 'VARCHAR(255) NOT NULL'),
                    ('enabled', 'BOOLEAN DEFAULT FALSE'),
                ])
                
            def down(self):
                self.drop_table('tesote_webhook_config')
    """
    
    # Override in subclasses
    version = None
    description = ""
    
    def __init__(self, cr):
        self.cr = cr
        self.executed_at = datetime.now()
        
        if not self.version:
            raise ValueError(f"Migration {self.__class__.__name__} must define a version")
    
    @abstractmethod
    def up(self):
        """Run the migration (like Rails migration up)"""
        pass
    
    @abstractmethod 
    def down(self):
        """Rollback the migration (like Rails migration down)"""
        pass
    
    # Table operations (Rails-like)
    def create_table(self, table_name, columns, **options):
        """
        Create a table with columns
        
        Args:
            table_name: Name of the table
            columns: List of tuples (column_name, column_definition)
            options: Additional table options
        """
        column_defs = []
        for name, definition in columns:
            column_defs.append(f"{name} {definition}")
        
        columns_sql = ",\n    ".join(column_defs)
        
        # Add common columns if not explicitly defined
        if not any(col[0] == 'create_date' for col in columns):
            columns_sql += ",\n    create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        if not any(col[0] == 'write_date' for col in columns):
            columns_sql += ",\n    write_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        if not any(col[0] == 'create_uid' for col in columns):
            columns_sql += ",\n    create_uid INTEGER REFERENCES res_users(id)"
        if not any(col[0] == 'write_uid' for col in columns):
            columns_sql += ",\n    write_uid INTEGER REFERENCES res_users(id)"
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        )
        """
        
        _logger.info(f"Creating table {table_name}")
        self.execute(sql)
        
        # Create indexes if specified
        if 'indexes' in options:
            for index in options['indexes']:
                self.add_index(table_name, index['columns'], 
                             unique=index.get('unique', False),
                             name=index.get('name'))
    
    def drop_table(self, table_name, if_exists=True):
        """Drop a table (Rails-like drop_table)"""
        if_exists_clause = "IF EXISTS" if if_exists else ""
        sql = f"DROP TABLE {if_exists_clause} {table_name} CASCADE"
        _logger.info(f"Dropping table {table_name}")
        self.execute(sql)
    
    def add_column(self, table_name, column_name, column_type, **options):
        """Add a column to existing table"""
        default = ""
        if 'default' in options:
            default = f"DEFAULT {options['default']}"
        
        null_constraint = ""
        if options.get('null', True) is False:
            null_constraint = "NOT NULL"
        
        sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type} {default} {null_constraint}"
        _logger.info(f"Adding column {column_name} to {table_name}")
        self.execute(sql)
    
    def remove_column(self, table_name, column_name):
        """Remove a column from table"""
        sql = f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name}"
        _logger.info(f"Removing column {column_name} from {table_name}")
        self.execute(sql)
    
    def rename_column(self, table_name, old_name, new_name):
        """Rename a column"""
        sql = f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}"
        _logger.info(f"Renaming column {old_name} to {new_name} in {table_name}")
        self.execute(sql)
    
    def add_index(self, table_name, columns, unique=False, name=None):
        """Add an index to table"""
        if isinstance(columns, str):
            columns = [columns]
        
        if not name:
            prefix = "uniq" if unique else "idx"
            name = f"{prefix}_{table_name}_{'_'.join(columns)}"
        
        unique_clause = "UNIQUE" if unique else ""
        columns_str = ", ".join(columns)
        
        sql = f"CREATE {unique_clause} INDEX IF NOT EXISTS {name} ON {table_name} ({columns_str})"
        _logger.info(f"Creating {'unique ' if unique else ''}index {name} on {table_name}")
        self.execute(sql)
    
    def remove_index(self, table_name, name=None, columns=None):
        """Remove an index"""
        if not name and columns:
            name = f"idx_{table_name}_{'_'.join(columns)}"
        
        if not name:
            raise ValueError("Must provide either index name or columns")
        
        sql = f"DROP INDEX IF EXISTS {name}"
        _logger.info(f"Dropping index {name}")
        self.execute(sql)
    
    # Data operations (Rails-like)
    def insert_data(self, table_name, data):
        """Insert data into table (like Rails create!)"""
        if not data:
            return
        
        if isinstance(data, dict):
            data = [data]
        
        for record in data:
            columns = list(record.keys())
            values = [f"'{v}'" if isinstance(v, str) else str(v) for v in record.values()]
            
            sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join(values)})
            ON CONFLICT DO NOTHING
            """
            self.execute(sql)
    
    def update_data(self, table_name, data, where_clause):
        """Update data in table"""
        set_clauses = []
        for key, value in data.items():
            if isinstance(value, str):
                set_clauses.append(f"{key} = '{value}'")
            else:
                set_clauses.append(f"{key} = {value}")
        
        sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
        _logger.info(f"Updating {table_name} where {where_clause}")
        self.execute(sql)
    
    def delete_data(self, table_name, where_clause):
        """Delete data from table"""
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        _logger.info(f"Deleting from {table_name} where {where_clause}")
        self.execute(sql)
    
    # Foreign key operations
    def add_foreign_key(self, from_table, from_column, to_table, to_column='id', name=None):
        """Add foreign key constraint"""
        if not name:
            name = f"fk_{from_table}_{from_column}"
        
        sql = f"""
        ALTER TABLE {from_table} 
        ADD CONSTRAINT {name} 
        FOREIGN KEY ({from_column}) 
        REFERENCES {to_table}({to_column})
        """
        _logger.info(f"Adding foreign key {name}")
        self.execute(sql)
    
    def remove_foreign_key(self, table_name, name):
        """Remove foreign key constraint"""
        sql = f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {name}"
        _logger.info(f"Removing foreign key {name}")
        self.execute(sql)
    
    # Utility methods
    def execute(self, sql):
        """Execute SQL with error handling"""
        try:
            self.cr.execute(sql)
            _logger.debug(f"Executed: {sql[:100]}...")
        except Exception as e:
            _logger.error(f"Migration SQL failed: {sql}")
            _logger.error(f"Error: {e}")
            raise
    
    def table_exists(self, table_name):
        """Check if table exists"""
        self.cr.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table_name,))
        return self.cr.fetchone()[0]
    
    def column_exists(self, table_name, column_name):
        """Check if column exists in table"""
        self.cr.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            )
        """, (table_name, column_name))
        return self.cr.fetchone()[0]
    
    def seed_data(self):
        """Override to provide seed data (like Rails db:seed)"""
        pass
    
    def __str__(self):
        return f"Migration {self.version}: {self.description or self.__class__.__name__}"