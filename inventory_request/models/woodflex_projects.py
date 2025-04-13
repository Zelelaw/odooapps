from datetime import timedelta

from num2words import num2words

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class WoodFlexProjects(models.Model):
    _name = 'wood.flex.projects'
    _description = 'Wood Flex Projects'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_name'

    def _get_employee_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    issued_by = fields.Many2one('hr.employee', required=True, default=_get_employee_id, index=True, string="Created By")
    project_id = fields.Char(string='Reference Number', required=True, copy=False, readonly=True, index=True,
                             default=lambda self: _('New'))
    project_name = fields.Char("Project Name", track_visibility="always")
    customer_name = fields.Char("Client Name", track_visibility="always")
    customer_site = fields.Char("Site", track_visibility="always")
    contractual_date = fields.Date("Contractual Date", default=fields.Datetime.now, readonly=True,
                                   track_visibility="always")
    contractual_end_date = fields.Date("Contract End Date", compute="_compute_contractual_end_date", store=True,
                                       track_visibility="always")
    contractual_amount = fields.Float("Contractual Amount", track_visibility="always")
    advance_amount = fields.Float("Advance Paid", track_visibility="always")
    remaining_amount = fields.Float("Remaining Amount", compute="_compute_remaining_amount", store=True,
                                    track_visibility="always")
    phone = fields.Char("Phone", track_visibility="always")
    email = fields.Char("Email", track_visibility="always")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company, track_visibility="always")
    state = fields.Selection(
        [('draft', 'Draft'), ('initialize', 'Initialization'), ('contract_signed', 'Contract Signed'),
         ('pro_completed', 'Project Completed'), ('pay_completed', 'Payment Completed'), ('cancelled', 'Cancelled')],
        'Status', required=True, copy=False, default='draft', track_visibility="always")
    terms_and_conditions = fields.Text(track_visibility="always")
    wood_flex_projects_lines = fields.One2many('wood.flex.projects.lines', 'wood_flex_projects_lines_id',
                                               string='Wood Flex Projects',
                                               track_visibility="always")

    wood_flex_projects_summary_lines = fields.One2many('wood.flex.projects.summary.lines',
                                                       'wood_flex_projects_summary_lines_id',
                                                       string='Wood Flex Projects Summary',
                                                       track_visibility="always")

    sub_total = fields.Float(string="Sub-Total", compute="_compute_amounts", store=True, default=0.0)
    vat = fields.Float(string="VAT(18%)", compute="_compute_amounts", store=True, default=0.0)
    total = fields.Float(string="Total", compute="_compute_amounts", store=True, default=0.0)
    price_allowance = fields.Float(string="Price Allowance", store=True, default=0.0)
    discount = fields.Float(string="Discount", store=True, default=0.0)
    delivery_fixing = fields.Float(string="Delivery and Fixing", store=True, default=0.0)
    photo = fields.Binary(string='Photo')
    design = fields.Many2many('ir.attachment', string='3D Design')
    include_vat = fields.Boolean(string="Include VAT", default=True)
    amount_in_word = fields.Char(compute="_compute_amount_in_word", string="Amount In Word", store=True)

    @api.depends('contractual_date')
    def _compute_contractual_end_date(self):
        for record in self:
            if record.contractual_date:
                record.contractual_end_date = record.contractual_date + timedelta(days=7)
            else:
                record.contractual_end_date = False

    @api.depends('contractual_date')
    def _compute_contractual_end_date(self):
        for record in self:
            if record.contractual_date:
                record.contractual_end_date = record.contractual_date + timedelta(days=7)
            else:
                record.contractual_end_date = False

    @api.constrains('contractual_end_date', 'contractual_date')
    def _check_contractual_end_date(self):
        for record in self:
            if record.contractual_end_date:
                if record.contractual_end_date < record.contractual_date or record.contractual_end_date <= fields.Date.today():
                    raise ValidationError(
                        "The Contractual End Date cannot be before the Contractual Date or today's date.")

    @api.model
    def default_get(self, fields_list):
        res = super(WoodFlexProjects, self).default_get(fields_list)
        res['contractual_date'] = fields.Datetime.now()
        return res

    @api.constrains('contractual_amount', 'advance_amount')
    def _check_advance_amount(self):
        for record in self:
            if record.advance_amount < (record.contractual_amount * 0.3):
                raise ValidationError("Advance amount must be at least 30% of the contractual amount.")

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def initialize(self):
        self.write({'state': 'initialize'})

    def contract_signed(self):
        self.write({'state': 'contract_signed'})

    def project_completed(self):
        self.write({'state': 'pro_completed'})

    def payment_completed(self):
        self.write({'state': 'pay_completed'})

    def cancel(self):
        self.write({'state': 'cancelled'})

    @api.model
    def create(self, vals):
        if vals.get('project_id', _('New')) == _('New'):
            vals['project_id'] = self.env['ir.sequence'].next_by_code('wood.flex.projects.sequence') or _('New')
        result = super(WoodFlexProjects, self).create(vals)
        return result

    @api.depends('wood_flex_projects_lines.amount', 'price_allowance', 'discount', 'delivery_fixing', 'include_vat')
    def _compute_amounts(self):
        for order in self:
            # Compute sub_total
            sub_total = sum(line.amount for line in order.wood_flex_projects_lines)
            # Apply discount
            if order.discount:
                sub_total -= (sub_total * (order.discount / 100))
            # delivery and fixing
            if order.delivery_fixing:
                sub_total += (sub_total * (order.delivery_fixing / 100))
            # Apply price allowance
            if order.price_allowance:
                sub_total += (sub_total * (order.price_allowance / 100))
            # Compute VAT and total
            vat = sub_total * 0.18 if order.include_vat else 0.0
            total = sub_total + vat
            # Update the order
            order.update({
                'sub_total': sub_total,
                'vat': vat,
                'total': total
            })

    @api.depends('contractual_amount', 'advance_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            if (rec.contractual_amount >= rec.advance_amount):
                rec.remaining_amount = rec.contractual_amount - rec.advance_amount
            else:
                raise ValidationError("Advance can't be greater than contractual amount")

    @api.depends('total')
    def _compute_amount_in_word(self):
        for order in self:
            if order.total:
                order.amount_in_word = num2words(order.total, lang='en').capitalize()


class WoodFlexProjectsLines(models.Model):
    _name = 'wood.flex.projects.lines'
    _description = 'Wood Flex Projects Lines'
    _rec_name = 'items'

    items = fields.Text(required=True, string="Item")
    material = fields.Text(string="Material")
    unit = fields.Many2one("uom.uom", string="UoM")
    color = fields.Char(string="Color")
    size = fields.Char(string="Size(WDH in (MM))")
    unit_price = fields.Float(string="Unit Price")
    quantity = fields.Float(string="Qty")
    amount = fields.Float(string="Amount")
    remark = fields.Char(string="Remark")

    wood_flex_projects_lines_id = fields.Many2one('wood.flex.projects', string='Wood Flex Projects Lines')

    @api.onchange('unit_price', 'quantity')
    def _onchange_calculate_amount(self):
        for line in self:
            line.amount = line.unit_price * line.quantity

    @api.model
    def create(self, vals):
        if 'unit_price' in vals and 'quantity' in vals:
            vals['amount'] = vals.get('unit_price', 0) * vals.get('quantity', 0)
        return super(WoodFlexProjectsLines, self).create(vals)

    def write(self, vals):
        for record in self:
            if 'unit_price' in vals or 'quantity' in vals:
                vals['amount'] = vals.get('unit_price', record.unit_price) * vals.get('quantity', record.quantity)
        return super(WoodFlexProjectsLines, self).write(vals)


class WoodFlexProjectsSummaryLines(models.Model):
    _name = 'wood.flex.projects.summary.lines'
    _description = 'Wood Flex Projects Summary Lines'
    _rec_name = 'item'

    item = fields.Many2one('product.template', required=True, string="Item")
    material = fields.Text(required=True, string="Material")
    quantity = fields.Float(required=True, string="Qty")
    amount = fields.Float(string="Amount")
    remark = fields.Char(string="Remark")

    wood_flex_projects_summary_lines_id = fields.Many2one('wood.flex.projects',
                                                          string='Wood Flex Projects Summary Lines')

    @api.onchange('amount', 'quantity')
    def _onchange_calculate_amount(self):
        for line in self:
            line.amount = line.amount * line.quantity

    @api.model
    def create(self, vals):
        if 'amount' in vals and 'quantity' in vals:
            vals['amount'] = vals.get('amount', 0) * vals.get('quantity', 0)
        return super(WoodFlexProjectsSummaryLines, self).create(vals)

    def write(self, vals):
        for record in self:
            if 'amount' in vals or 'quantity' in vals:
                vals['amount'] = vals.get('amount', record.amount) * vals.get('quantity', record.quantity)
        return super(WoodFlexProjectsSummaryLines, self).write(vals)
