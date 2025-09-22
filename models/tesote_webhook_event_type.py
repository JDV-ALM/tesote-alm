# -*- coding: utf-8 -*-
from odoo import models, fields


class TesoteWebhookEventType(models.Model):
    _name = 'tesote.webhook.event.type'
    _description = 'Tesote Webhook Event Type'
    _rec_name = 'name'

    name = fields.Char(string='Event Type', required=True)
    description = fields.Text(string='Description')
