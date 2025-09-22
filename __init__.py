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