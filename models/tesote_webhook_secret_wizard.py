from odoo import models, fields, api, _


class TesoteWebhookSecretWizard(models.TransientModel):
    """Wizard to display webhook secret key in a copyable format."""
    
    _name = 'tesote.webhook.secret.wizard'
    _description = 'Webhook Secret Key Display Wizard'
    
    webhook_config_id = fields.Many2one(
        'tesote.webhook.config',
        string='Webhook Configuration',
        readonly=True
    )
    
    secret_key = fields.Char(
        string='Secret Key',
        readonly=True,
        help='Copy this secret key to your tesote.com webhook configuration'
    )
    
    webhook_url = fields.Char(
        string='Webhook URL',
        readonly=True,
        help='Copy this URL to your tesote.com webhook endpoint configuration'
    )
    
    instructions = fields.Html(
        string='Instructions',
        default=lambda self: _("""
        <p><strong>How to configure webhooks in equipo.tesote.com:</strong></p>
        <ol>
            <li>Copy the <strong>Webhook URL</strong> above</li>
            <li>Copy the <strong>Secret Key</strong> above</li>
            <li>Go to <a href="https://equipo.tesote.com" target="_blank">equipo.tesote.com</a></li>
            <li>Navigate to Settings → Integrations → Webhooks</li>
            <li>Create a new webhook or edit existing one</li>
            <li>Paste the <strong>Webhook URL</strong> in the endpoint field</li>
            <li>Paste the <strong>Secret Key</strong> in the secret field</li>
            <li>Select the events you want to subscribe to</li>
            <li>Save your webhook configuration</li>
        </ol>
        <p><em>Keep this secret key secure and do not share it publicly.</em></p>
        """),
        readonly=True
    )