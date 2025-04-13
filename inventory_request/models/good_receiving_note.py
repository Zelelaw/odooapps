from odoo import models, fields, _, api


class GoodReceivingNote(models.Model):
    _name = 'good.receiving.note'
    _description = 'Good Receiving Note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'serial_number'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    prepared_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True,
                                  string="Prepared By")

    approved_by = fields.Many2one('hr.employee', index=True,
                                  string="Approved By", track_visibility="always")
    serial_number = fields.Char(string='No.', required=True, copy=False, readonly=True, index=True,
                                default=lambda self: _('New'))
    local_purchase_order_number = fields.Many2one('local.purchase.order', 'LPO No./Invoice No.',
                                                  domain="[('state', '=', 'purchased')]", track_visibility="always")
    date = fields.Datetime(string='Date', track_visibility="always", default=fields.Datetime.now, readonly=True)
    phone_number = fields.Char(string='Phone Number', track_visibility="always")
    supplier_name = fields.Many2one('supplier.list', string='Name of Supplier', track_visibility="always")
    for_project = fields.Many2one(related='local_purchase_order_number.for_project', string="For Project",
                                  track_visibility="always",
                                  domain="[('state', '=', 'contract_signed')]")
    total = fields.Float(related='local_purchase_order_number.total', string='Total')

    delivered_by = fields.Many2one('hr.employee', index=True,
                                   string="Delivered By", track_visibility="always")
    good_receiving_note_line = fields.One2many('good.receiving.note.lines', 'good_receiving_note_line_id',
                                               string='Good Receiving Note Lines', track_visibility="always")

    receipt_attachment = fields.Many2many('ir.attachment', string='Receipt Attachment')
    payment_type = fields.Selection(
        [('cash_on_delivery', 'Cash on Delivery'), ('paid', 'Paid'), ('credit', 'Credit')],
        'Payment Type', copy=False, default='cash_on_delivery', track_visibility="always")
    advance_payment = fields.Float('Advance Payment')

    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval', 'Manager Approval'),
         ('waiting_purchaser_approval', 'Purchaser Approval'), ('waiting_finance_approval', 'Finance Approval'),
         ('approved', 'Approved'),
         ('received', 'Received'), ('cancelled', 'Cancelled')],
        'Status', required=True, copy=False, default='draft', track_visibility="always")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)

    @api.onchange('local_purchase_order_number')
    def _onchange_local_purchase_order_number(self):
        if self.local_purchase_order_number:
            self.good_receiving_note_line = [(5, 0, 0)]  # Clears existing lines
            lines = []
            for line in self.local_purchase_order_number.local_purchase_order_line:
                lines.append((0, 0, {
                    'item': line.item.id,
                    'unit': line.unit.id,
                    'quantity': line.quantity,
                    'unit_price': line.rate,
                    'amount': line.amount,
                    'supplier': line.supplier_list.name,
                    'remark': line.remark,
                }))
            self.good_receiving_note_line = lines

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def send_for_approval(self):
        self.write({'state': 'waiting_approval'})

    def send_for_purchaser(self):
        self.write({'state': 'waiting_purchaser_approval'})

    def send_for_finance(self):
        self.write({'state': 'waiting_finance_approval'})

    def approved(self):
        self.write({'state': 'approved'})

    def delivered(self):
        self.write({'state': 'received'})

    def cancel(self):
        self.write({'state': 'cancelled'})

    @api.model
    def create(self, vals):
        if vals.get('serial_number', _('New')) == _('New'):
            vals['serial_number'] = self.env['ir.sequence'].next_by_code('good.receiving.note.sequence') or _('New')

        result = super(GoodReceivingNote, self).create(vals)
        return result


class GoodReceivingNoteLines(models.Model):
    _name = 'good.receiving.note.lines'
    _description = 'Good Receiving Note Lines'
    _rec_name = 'item'

    item = fields.Many2one('product.template', required=True, string="Name of Item")
    unit = fields.Many2one(related='item.uom_id', string="Unit", store=True)
    quantity = fields.Integer(required=True, string="Qty")
    received_quantity = fields.Float(required=True, string="Received Qty", default=0.0)
    unit_price = fields.Float(required=True, string="Unit Price")
    amount = fields.Float(required=True, string="Amount")
    supplier = fields.Char('Supplier')
    remark = fields.Char(string="Remark")
    good_receiving_note_line_id = fields.Many2one('good.receiving.note', string='Good Receiving Note Lines')
