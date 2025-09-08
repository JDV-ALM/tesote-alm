#!/bin/bash
set -e

# Run the original Odoo entrypoint
exec /usr/local/bin/odoo "$@"