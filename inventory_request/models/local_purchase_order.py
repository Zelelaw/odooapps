from num2words import num2words

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class LocalPurchaseOrder(models.Model):
    _name = 'local.purchase.order'
    _description = 'Local Purchase Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'LPO_Number'

    def _get_employee_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    issued_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True, string="Issued By")
    order_date = fields.Date(required=True, index=True, string="Order Date", default=fields.Datetime.now)
    LPO_Number = fields.Char(string='LPO Number', required=True, copy=False, readonly=True, index=True,
                             default=lambda self: _('New'))
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    state = fields.Selection(
        [('draft', 'Draft'), ('purchaser', 'Purchaser Approval'), ('account', 'CFO Approval'),
         ('manager', 'Manager\'s Approval'),
         ('confirmed', 'Confirmed'), ('purchased', 'Item Purchased'), ('cancelled', 'Cancelled')],
        'Status', required=True, copy=False, default='draft', track_visibility="always")
    payed_amount = fields.Float(string="Payed Amount", track_visibility="always")
    supplier = fields.Many2one('res.partner', string="Supplier", track_visibility="always")
    for_project = fields.Many2one('wood.flex.projects', string="For Project", track_visibility="always",
                                  domain="[('state', '=', 'contract_signed')]")
    # for_purchase_order_requisition = fields.Many2one('purchase.order.requisition', 'For Purchase Order Requisition')
    narration = fields.Text(track_visibility="always")
    local_purchase_order_line = fields.One2many('local.purchase.order.lines', 'local_purchase_order_line_id',
                                                string='Local Purchase Order',
                                                track_visibility='onchange', required=True)
    sub_total = fields.Float(string="Sub-Total", compute="_compute_amounts", store=True, default=0.0)
    vat = fields.Float(string="VAT(18%)", compute="_compute_amounts", store=True, default=0.0)
    # less = fields.Float(string="Less(WHT)", compute="_compute_amounts", store=True, default=0.0)
    total = fields.Float(string="Total", compute="_compute_amounts", store=True, default=0.0)
    include_vat = fields.Boolean(string="Include VAT", default=True)
    amount_in_word = fields.Char(compute="_compute_amount_in_word", string="Amount In Word", store=True)

    @api.constrains('payed_amount', 'total')
    def _check_payed_amount(self):
        for record in self:
            if record.state == "account":
                if record.payed_amount > record.total:
                    raise ValidationError("Payed amount must be less than total amount.")

    @api.constrains('local_purchase_order_line')
    def _check_local_purchase_order_line(self):
        for order in self:
            if not order.local_purchase_order_line:
                raise ValidationError(_("A Local Purchase Order must have at least one line item."))

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def send_for_manager_approval(self):
        self.write({'state': 'purchaser'})

    def send_for_accountant_approval(self):
        self.write({'state': 'manager'})

    def send_for_purchaser_approval(self):
        self.write({'state': 'account'})

    def confirm(self):
        self.write({'state': 'confirmed'})

    def purchased(self):
        self.write({'state': 'purchased'})

    def cancel(self):
        self.write({'state': 'cancelled'})

    @api.model
    def create(self, vals):
        if 'local_purchase_order_line' in vals and not vals['local_purchase_order_line']:
            raise ValidationError(_("A Local Purchase Order must have at least one line item."))

        if vals.get('LPO_Number', _('New')) == _('New'):
            vals['LPO_Number'] = self.env['ir.sequence'].next_by_code('local.purchase.order.sequence') or _('New')

        result = super(LocalPurchaseOrder, self).create(vals)
        return result

    def write(self, vals):
        if 'local_purchase_order_line' in vals and not vals['local_purchase_order_line']:
            raise ValidationError(_("A Local Purchase Order must have at least one line item."))

        return super(LocalPurchaseOrder, self).write(vals)

    @api.depends('local_purchase_order_line.amount', 'include_vat')
    def _compute_amounts(self):
        for order in self:
            sub_total = sum(line.amount or 0.0 for line in order.local_purchase_order_line)
            vat = sub_total * 0.18 if order.include_vat else 0.0
            total = sub_total + vat
            order.update({
                'sub_total': sub_total,
                'vat': vat,
                'total': total
            })

    @api.depends('total')
    def _compute_amount_in_word(self):
        for order in self:
            if order.total:
                order.amount_in_word = num2words(order.total, lang='en').capitalize()


class LocalPurchaseOrderLines(models.Model):
    _name = 'local.purchase.order.lines'
    _description = 'Local Purchase Order Lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'item'

    item = fields.Many2one('product.template', required=True, string="Item", track_visibility="always")
    unit = fields.Many2one(related='item.uom_id', string="Unit", store=True, track_visibility="always")
    rate = fields.Float(string="Unit Price", track_visibility="always")
    quantity = fields.Float(string="Qty", track_visibility="always", default=1.0)
    amount = fields.Float(string="Amount", readonly=True)
    remark = fields.Char(string="Remark", track_visibility="always")
    supplier_list = fields.Many2one('supplier.list', string="Supplier", track_visibility="always")

    local_purchase_order_line_id = fields.Many2one('local.purchase.order', string='Local Purchase Order Lines')

    @api.constrains('quantity', 'rate')
    def _check_payed_amount(self):
        for record in self:
            if record.quantity <= 0 or record.rate <= 0:
                raise ValidationError("Quantity or Unit Price can't be Zero.")

    @api.depends('local_purchase_order_line_id.state')
    def _compute_readonly_fields(self):
        for line in self:
            readonly = line.local_purchase_order_line_id.state == 'draft'
            line.update({
                'rate': {'readonly': readonly},
                'quantity': {'readonly': readonly},
                'amount': {'readonly': readonly},
            })

    @api.onchange('rate', 'quantity')
    def onchange_calculate_amount(self):
        for line in self:
            line.amount = line.rate * line.quantity

    @api.model
    def create(self, vals):
        if 'rate' in vals and 'quantity' in vals:
            vals['amount'] = vals.get('rate', 0) * vals.get('quantity', 0)
        return super(LocalPurchaseOrderLines, self).create(vals)

    def write(self, vals):
        for record in self:
            if 'rate' in vals or 'quantity' in vals:
                vals['amount'] = vals.get('rate', record.rate) * vals.get('quantity', record.quantity)
        return super(LocalPurchaseOrderLines, self).write(vals)
