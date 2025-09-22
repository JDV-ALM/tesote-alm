# Copyright 2024 tesote.com
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Tesote Account Model.
Represents financial accounts synchronized from Tesote API.
"""

import logging
from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class TesoteAccount(models.Model):
    """Financial account from Tesote API."""
    
    _name = 'tesote.account'
    _inherit = 'tesote.binding'
    _description = 'Tesote Account'
    _rec_name = 'name'
    
    name = fields.Char(
        string='Account Name',
        required=True,
        help='Display name of the account'
    )
    
    tesote_id = fields.Char(
        string='Tesote ID',
        required=True,
        readonly=True,
        index=True,
        help='Unique identifier in Tesote system'
    )
    
    backend_id = fields.Many2one(
        'tesote.backend',
        string='Backend',
        required=True,
        ondelete='cascade',
        help='Tesote backend instance'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        help='Linked partner/customer'
    )
    
    transaction_count = fields.Integer(
        string='Transaction Count',
        compute='_compute_transaction_count',
        store=False
    )
    
    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        """Compute transaction count."""
        for account in self:
            account.transaction_count = len(account.transaction_ids)
    
    def action_view_transactions(self):
        """Open transactions view for this account."""
        self.ensure_one()
        return {
            'name': _('Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'tesote.transaction',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('account_id', '=', self.id)],
            'context': {'default_account_id': self.id},
        }
    
    bank_name = fields.Char(
        string='Bank Name',
        help='Name of the financial institution'
    )
    
    legal_entity_name = fields.Char(
        string='Legal Entity',
        help='Legal entity owning the account'
    )
    
    account_data = fields.Text(
        string='Account Data',
        help='Additional account data in JSON format'
    )
    
    balance = fields.Float(
        string='Balance',
        digits='Account',
        help='Current account balance'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        help='Account currency'
    )
    
    tesote_created_at = fields.Datetime(
        string='Created in Tesote',
        readonly=True,
        help='Creation date in Tesote system'
    )
    
    tesote_updated_at = fields.Datetime(
        string='Updated in Tesote',
        readonly=True,
        help='Last update date in Tesote system'
    )
    
    transaction_ids = fields.One2many(
        'tesote.transaction',
        'account_id',
        string='Transactions'
    )
    
    transaction_count = fields.Integer(
        string='Transaction Count',
        compute='_compute_transaction_count'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    _sql_constraints = [
        (
            'tesote_id_backend_uniq',
            'UNIQUE(tesote_id, backend_id)',
            'Tesote ID must be unique per backend!'
        ),
    ]
    
    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        """Compute number of transactions."""
        for account in self:
            account.transaction_count = len(account.transaction_ids)
    
    def sync_from_tesote(self):
        """
        Synchronize account data from Tesote API.
        
        Fetches latest account information and updates local record.
        """
        self.ensure_one()
        
        # For now, just update from API
        from ..components.adapter import TesoteAdapter
        adapter = TesoteAdapter(self.backend_id)
        
        # Get account data from API
        account_data = adapter.get_account(self.tesote_id)
        if account_data:
            self.update_from_tesote(account_data)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Account synchronized successfully'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def import_transactions(self, date_from=None, date_to=None):
        """
        Import transactions for this account.
        
        Args:
            date_from: Start date for import
            date_to: End date for import
        """
        self.ensure_one()
        
        return self.backend_id.import_transactions(
            account_ids=[self.id],
            date_from=date_from,
            date_to=date_to
        )
    
    def action_view_transactions(self):
        """
        Open view to display account transactions.
        
        Returns:
            Action dictionary to open transaction list
        """
        self.ensure_one()
        
        return {
            'name': _('Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'tesote.transaction',
            'view_mode': 'list,form',
            'domain': [('account_id', '=', self.id)],
            'context': {
                'default_account_id': self.id,
            }
        }
    
    @api.model
    def _parse_tesote_datetime(self, date_string):
        """
        Parse Tesote API datetime string to Odoo format.
        Handles ISO format with timezone: 2025-03-05T09:41:36-05:00
        """
        if not date_string:
            return False
        try:
            # Parse ISO format with timezone
            if 'T' in date_string:
                # Remove timezone info for Odoo
                if '+' in date_string or date_string[-6] == '-':
                    date_string = date_string[:-6]  # Remove timezone offset
                elif 'Z' in date_string:
                    date_string = date_string[:-1]  # Remove Z
                # Convert to Odoo datetime format
                dt = datetime.fromisoformat(date_string)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return date_string
        except Exception as e:
            _logger.warning(f"Could not parse date {date_string}: {e}")
            return False

    @api.model
    def create_from_tesote(self, backend, data):
        """
        Create account from Tesote API data.
        
        Args:
            backend: tesote.backend record
            data: Dictionary with account data from API
            
        Returns:
            Created tesote.account record
        """
        vals = {
            'backend_id': backend.id,
            'tesote_id': data['id'],
            'name': data['name'],
            'bank_name': data.get('bank', {}).get('name'),
            'legal_entity_name': data.get('legal_entity', {}).get('name'),
            'account_data': str(data.get('data', {})),
            'tesote_created_at': self._parse_tesote_datetime(data.get('tesote_created_at')),
            'tesote_updated_at': self._parse_tesote_datetime(data.get('tesote_updated_at')),
        }
        
        # Set balance if available - check multiple possible field names
        balance = (
            data.get('balance') or 
            data.get('current_balance') or 
            data.get('available_balance') or
            data.get('balance_amount') or
            0.0
        )
        if balance:
            vals['balance'] = float(balance)
        
        # Set currency if available
        if 'currency' in data:
            currency = self.env['res.currency'].search([
                ('name', '=', data['currency'])
            ], limit=1)
            if currency:
                vals['currency_id'] = currency.id
        
        return self.create(vals)
    
    def update_from_tesote(self, data):
        """
        Update account from Tesote API data.
        
        Args:
            data: Dictionary with account data from API
        """
        self.ensure_one()
        
        vals = {
            'name': data['name'],
            'bank_name': data.get('bank', {}).get('name'),
            'legal_entity_name': data.get('legal_entity', {}).get('name'),
            'account_data': str(data.get('data', {})),
            'tesote_updated_at': self._parse_tesote_datetime(data.get('tesote_updated_at')),
        }
        
        # Update balance if available - check multiple possible field names
        balance = (
            data.get('balance') or 
            data.get('current_balance') or 
            data.get('available_balance') or
            data.get('balance_amount') or
            0.0
        )
        if balance:
            vals['balance'] = float(balance)
        
        # Update currency if available
        if 'currency' in data:
            currency = self.env['res.currency'].search([
                ('name', '=', data['currency'])
            ], limit=1)
            if currency:
                vals['currency_id'] = currency.id
        
        self.write(vals)