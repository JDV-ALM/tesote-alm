# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Tesote Binding Model.
Base class for all Tesote synchronized models.
"""

from odoo import fields, models


class TesoteBinding(models.AbstractModel):
    """Abstract model for Tesote bindings."""

    _name = "tesote.binding"
    _description = "Tesote Binding"

    backend_id = fields.Many2one(
        "tesote.backend",
        string="Backend",
        required=True,
        ondelete="cascade",
        help="Tesote backend instance",
    )

    tesote_id = fields.Char(
        string="Tesote ID",
        required=True,
        readonly=True,
        index=True,
        help="External ID in Tesote system",
    )

    sync_date = fields.Datetime(
        string="Last Sync Date", help="Date of last synchronization with Tesote"
    )

    sync_cursor = fields.Char(string="Sync Cursor", help="Cursor position for incremental sync")

    def resync(self):
        """Force resynchronization with Tesote."""
        raise NotImplementedError
