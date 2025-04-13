from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_model = fields.Char(string='Product Model')
    product_serial = fields.Char('Product Serial')
    store = fields.Selection([
        ('all_store', 'Temporary Store'),
        ('permanent', 'Main'),
        ('consumable', 'Tools')],
        string='Store', required=True, readonly=False, default='all_store')


# class AccountMove(models.Model):
#     _inherit = 'account.move'
#
#     bank_account = fields.Many2one('account.journal', string='Bank')
#     check_number = fields.Char('Check Number')
#
