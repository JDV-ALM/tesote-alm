#!/usr/bin/env python3
# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Test runner that properly mocks Odoo before importing any modules.
This ensures tests can run without Odoo installation.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Mock Odoo modules BEFORE any imports
from unittest.mock import MagicMock

print("Setting up Odoo mocks...")

# Mock all Odoo modules
sys.modules['odoo'] = MagicMock()
sys.modules['odoo.exceptions'] = MagicMock()
sys.modules['odoo.models'] = MagicMock()
sys.modules['odoo.fields'] = MagicMock()
sys.modules['odoo.api'] = MagicMock()
sys.modules['odoo.tools'] = MagicMock()
sys.modules['odoo.http'] = MagicMock()
sys.modules['odoo._'] = lambda x: x  # Translation function

# Create mock classes
class MockModel:
    """Mock Odoo Model class."""
    pass

class MockFields:
    """Mock Odoo Fields."""
    Char = MagicMock()
    Text = MagicMock()
    Integer = MagicMock()
    Float = MagicMock()
    Boolean = MagicMock()
    Date = MagicMock()
    Datetime = MagicMock()
    Selection = MagicMock()
    Many2one = MagicMock()
    One2many = MagicMock()
    Many2many = MagicMock()

class MockApi:
    """Mock Odoo API decorators."""
    @staticmethod
    def model(func):
        return func
    
    @staticmethod
    def depends(*args):
        def decorator(func):
            return func
        return decorator
    
    @staticmethod
    def constrains(*args):
        def decorator(func):
            return func
        return decorator

class MockUserError(Exception):
    """Mock UserError exception."""
    pass

# Set up the mocks
sys.modules['odoo'].models.Model = MockModel
sys.modules['odoo'].fields = MockFields()
sys.modules['odoo'].api = MockApi()
sys.modules['odoo.exceptions'].UserError = MockUserError
sys.modules['odoo']._ = lambda x: x

print("Odoo mocks configured successfully")

# Now we can safely import pytest and run tests
import pytest

def run_tests():
    """Run pytest tests with proper configuration."""
    print("\n" + "="*60)
    print("RUNNING TESOTE CONNECTOR TESTS")
    print("="*60 + "\n")
    
    # Temporarily rename __init__.py to avoid import issues
    init_file = Path(__file__).parent / '__init__.py'
    init_backup = Path(__file__).parent / '__init__.py.bak'
    
    if init_file.exists():
        init_file.rename(init_backup)
    
    try:
        # Configure pytest arguments
        args = [
            'tests/',
            '-v',
            '--color=yes',
            '--tb=short',
            '-p', 'no:cacheprovider',  # Disable cache
            '--import-mode=importlib',
        ]
        
        # Run pytest
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            print("\n" + "="*60)
            print("✓ ALL PYTEST TESTS PASSED")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("✗ SOME PYTEST TESTS FAILED")
            print("="*60)
        
        return exit_code
    finally:
        # Restore __init__.py
        if init_backup.exists():
            init_backup.rename(init_file)

if __name__ == "__main__":
    try:
        sys.exit(run_tests())
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure pytest is installed: pip install pytest responses freezegun")
        sys.exit(1)