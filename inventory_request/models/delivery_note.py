from odoo import models, fields, api, _


class DeliveryNote(models.Model):
    _name = 'delivery.note'
    _description = 'Delivery Note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'serial_number'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    prepared_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True,
                                  string="Name")
    serial_number = fields.Char(string='Serial Number', required=True, copy=False, readonly=True, index=True,
                                default=lambda self: _('New'))
    date = fields.Datetime(string='Date')
    delivery_note_line = fields.One2many('delivery.note.lines', 'delivery_note_line_id',
                                         string='Delivery Note',
                                         track_visibility="always")
    received_by = fields.Many2one('res.partner', string="M/S", track_visibility="always")
    sign = fields.Char(string='Signature')
    for_project = fields.Many2one('wood.flex.projects', string="For Project", track_visibility="always",
                                  domain="[('state', '=', 'contract_signed')]")
    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval', 'Waiting Approval'), ('approved', 'Approved'),
         ('delivered', 'Delivered'), ('cancelled', 'Cancelled')],
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
            vals['serial_number'] = self.env['ir.sequence'].next_by_code('delivery.note.sequence') or _('New')

        result = super(DeliveryNote, self).create(vals)
        return result


class DeliveryNOteLines(models.Model):
    _name = 'delivery.note.lines'
    _description = 'Delivery Note Lines'

    item = fields.Many2one('product.template', required=True, string="Description")
    quantity = fields.Integer(required=True, string="Qty")
    delivery_note_line_id = fields.Many2one('delivery.note', string='Delivery Note Lines')
