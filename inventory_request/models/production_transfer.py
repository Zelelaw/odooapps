from odoo import models, fields, _, api


class ProductionTransfer(models.Model):
    _name = 'production.transfer'
    _description = 'Production Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference_number'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    prepared_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True,
                                  string="Prepared By")
    reference_number = fields.Char(string='Reference Number', required=True, copy=False, readonly=True, index=True,
                                   default=lambda self: _('New'))
    date = fields.Datetime(string='Date')
    site = fields.Char(string='Site')
    client_name = fields.Char(string='Client Name')
    for_project = fields.Many2one('wood.flex.projects', string="Project", track_visibility="always",
                                  domain="[('state', '=', 'contract_signed')]")
    production_transfer_line = fields.One2many('production.transfer.lines', 'production_transfer_line_id',
                                               string='Production Transfer',
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
        if vals.get('reference_number', _('New')) == _('New'):
            vals['reference_number'] = self.env['ir.sequence'].next_by_code('production.transfer.sequence') or _('New')

        result = super(ProductionTransfer, self).create(vals)
        return result


class ProductionTransferLines(models.Model):
    _name = 'production.transfer.lines'
    _description = 'Production Transfer Lines'

    item = fields.Many2one('product.template', required=True, string="Item Description")
    quantity = fields.Integer(required=True, string="Qty")
    unit = fields.Many2one("uom.uom", string="UoM")
    remain_work = fields.Char(required=True, string="Remain Work")
    remark = fields.Char(required=True, string="Remark")
    production_transfer_line_id = fields.Many2one('production.transfer', string='Production Transfer Lines')
