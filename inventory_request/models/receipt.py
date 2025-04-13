from odoo import models, fields, _, api


class Receipt(models.Model):
    _name = "woodfelx.receipt"
    _description = 'Wood Flex Receipts'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'serial_number'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    prepared_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True,
                                  string="Prepared By")
    serial_number = fields.Char(string='Serial Number', required=True, copy=False, readonly=True, index=True,
                                default=lambda self: _('New'))
    date = fields.Datetime(string='Date')
    client = fields.Char(string='Client')
    site = fields.Char(string='Site')
    items = fields.Many2one('product.template', string='Items')
    contract_amount = fields.Char(string='Contract Amount')
    for_project = fields.Many2one('wood.flex.projects', string="For Project", track_visibility="always", domain="[('state', '=', 'contract_signed')]")
    payment_number = fields.Char(string='Payment Number')
    amount_in_word = fields.Char(string='Amount in Word')
    balance = fields.Char(string='Balance')
    sign = fields.Char(string='Sign')
    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval', 'Waiting Approval'), ('approved', 'Approved'),
         ('collected', 'Collected'), ('cancelled', 'Cancelled')],
        'Status', required=True, copy=False, default='draft', track_visibility="always")

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def send_for_approval(self):
        self.write({'state': 'waiting_approval'})

    def approved(self):
        self.write({'state': 'approved'})

    def delivered(self):
        self.write({'state': 'delivered'})

    def cancel(self):
        self.write({'state': 'cancelled'})

    @api.model
    def create(self, vals):
        if vals.get('serial_number', _('New')) == _('New'):
            vals['serial_number'] = self.env['ir.sequence'].next_by_code('woodfelx.receipt.sequence') or _('New')

        result = super(Receipt, self).create(vals)
        return result
