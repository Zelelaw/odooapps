from odoo import models, fields


class Receipt(models.Model):
    _name = "supplier.list"
    _description = 'Supplier List'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    created_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True,
                                 string="Created By")
    name = fields.Char(string='Name')
    address = fields.Char(string='Address')
    phone = fields.Char("Phone")
    email = fields.Char("Email")
