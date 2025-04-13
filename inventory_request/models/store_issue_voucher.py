from odoo import models, fields, _, api


class StoreIssueVoucher(models.Model):
    _name = 'store.issue.voucher'
    _description = 'Store Issue Voucher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'serial_number'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    prepared_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True,
                                  string="Prepared By")

    # issued_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True,
    #                             string="Issued By", track_visibility="always")
    team_leader_name = fields.Many2one('hr.employee', required=True, index=True,
                                       string="Team Leader Name")
    serial_number = fields.Char(string='Store Issue No.', required=True, copy=False, readonly=True, index=True,
                                default=lambda self: _('New'))
    date = fields.Datetime(string='Date')
    for_project = fields.Many2one('wood.flex.projects', string="For Project", track_visibility="always", domain="[('state', '=', 'contract_signed')]")
    section_name = fields.Char(string='Section Name')
    client_name = fields.Many2one('res.partner', string='Client Name/Project')
    item_location = fields.Char(string='Item Location')
    store_issue_voucher_line = fields.One2many('store.issue.voucher.lines', 'store_issue_voucher_line_id',
                                               string='Store Issue Voucher',
                                               track_visibility="always")
    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval', 'Waiting Approval'), ('approved', 'Approved'),
         ('delivered', 'Delivered'), ('return', 'Return'), ('cancelled', 'Cancelled')],
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

    def returned(self):
        self.write({'state': 'return'})

    def cancel(self):
        self.write({'state': 'cancelled'})

    @api.model
    def create(self, vals):
        if vals.get('serial_number', _('New')) == _('New'):
            vals['serial_number'] = self.env['ir.sequence'].next_by_code('store.issue.voucher.sequence') or _('New')

        result = super(StoreIssueVoucher, self).create(vals)
        return result


class StoreIssueVoucherLines(models.Model):
    _name = 'store.issue.voucher.lines'
    _description = 'Store Issue Voucher Lines'

    item = fields.Many2one('product.template', required=True, string="Name of Item")
    unit = fields.Many2one("uom.uom", string="Unit")
    quantity = fields.Integer(required=True, string="Qty")
    size = fields.Float(required=True, string="Size")
    remark = fields.Char(required=True, string="Remark")
    store_issue_voucher_line_id = fields.Many2one('store.issue.voucher', string='Store Issue Voucher Lines')
