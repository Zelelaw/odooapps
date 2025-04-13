from odoo import models, fields, _, api


class PaymentVoucher(models.Model):
    _name = 'payment.voucher'
    _description = 'Payment Receipts'
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
    supplier = fields.Many2one('supplier.list', string='Supplier')
    approved_by = fields.Many2one('hr.employee', string='Approved By')
    for_project = fields.Many2one('wood.flex.projects', string="For Project", track_visibility="always",
                                  domain="[('state', '=', 'contract_signed')]")
    payment_voucher_line = fields.One2many('payment.voucher.lines', 'payment_voucher_line_id',
                                           string='Payment Voucher',
                                           track_visibility="always")
    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval', 'Waiting Approval'), ('approved', 'Approved'), ('payed', 'Payed'),
         ('cancelled', 'Cancelled')],
        'Status', required=True, copy=False, default='draft', track_visibility="always")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)

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
            vals['serial_number'] = self.env['ir.sequence'].next_by_code('payment.voucher.sequence') or _('New')

        result = super(PaymentVoucher, self).create(vals)
        return result


class PaymentVoucherLines(models.Model):
    _name = 'payment.voucher.lines'
    _description = 'Payment Receipts Lines'

    item = fields.Many2one('product.template', required=True, string="Name of Item")
    unit = fields.Many2one("uom.uom", string="Unit")
    quantity = fields.Integer(required=True, string="Qty")
    unit_price = fields.Float(required=True, string="Unit Price")
    amount = fields.Float(required=True, string="Amount")
    remark = fields.Char(required=True, string="Remark")
    payment_voucher_line_id = fields.Many2one('payment.voucher', string='Payment Voucher Lines')
