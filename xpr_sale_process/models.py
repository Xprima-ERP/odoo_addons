# -*- coding: utf-8 -*-

import datetime
from openerp.exceptions import AccessError
from openerp import models, fields, api


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = "sale.order"

    @api.depends('starting_date', 'date_order')
    def _get_renew_date(self):
        for order in self:

            date = (
                order.starting_date or
                order.date_order)

            if date:
                date = fields.Date.from_string(date)
            else:
                date = datetime.datetime.now()

            date = fields.Date.to_string(date + datetime.timedelta(days=365))

            order.renew_date = date

    state = fields.Selection(
        [
            ('draft', 'Draft Quotation'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('need_manager_approval', 'Need Manager Approval'),
            ('manager_approved', 'Manager Approved'),
            ('manager_not_approved', 'Manager Declined'),
            ('contract_not_presented', 'Not Presented to Customer'),
            ('contract_approved', 'Approved by Customer'),
            ('contract_not_approved', 'Not Approved by Customer'),
            ('need_availability_check', 'Need Availability Check'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('done', 'Done'),
        ],
        'Status',
        readonly=True,
        copy=False,
        help="Gives the status of the quotation or sales order.\
        Quotations require approval from management and customer to be contracts.",
        select=True
    )

    order_line = fields.One2many(
        'sale.order.line',
        'order_id',
        'Order Lines',
        readonly=True,
        states={
            'draft': [('readonly', False)],
            #'manager_not_approved': [('readonly', False)],
            #'contract_not_approved': [('readonly', False)],
            #'need_availability_check': [('readonly', False)],
            #'need_manager_approval': [('readonly', False)],

            #'sent': [('readonly', False)],
            #'invoice_except': [('readonly', False)],
            #'done': [('readonly', False)],
            #'manager_approved,': [('readonly', False)],
            #'contract_not_presented,': [('readonly', False)],
            #'contract_approved': [('readonly', False)],
        },
        copy=True
    )

    renew_date = fields.Date(string="Renew Date", compute=_get_renew_date, store=True)

    def check_manager_approval_needed(self):

        if self.solution_discount:
            return True

        for line in self.order_line:
            if line.discount:
                return True

        return False

    def check_product_availability_needed(self):
        """
        Return True if product availability check is required and False if not.
        """

        if self.category.approval_group:
            return True

        return False

    def has_rights_to_approve(self):
        """
        Return True if the user triggering this method has the right to approve
        the associated quote. The user has the right if he is some admin
        or if as a sales manager, is also the manager of
        the salesperson associated to the quote. An AccessError exception is
        raised if sales manager is trying to approve a quote outside his team
        """

        discount_all = self.env.ref('xpr_sale_process.discount_all')
        sales_manager = self.env.ref('base.group_sale_manager')

        is_sales_manager = False
        for group in self.env.user.groups_id:
            if group.id == discount_all.id:
                return True

            if group.id == sales_manager.id:
                is_sales_manager = True
                break

        if not is_sales_manager:
            return False

        args = [("user_id", "=", self.env.user.id)]
        hr_approver = self.env["hr.employee"].search(args)
        args = [("user_id", "=", self.user_id.id)]
        hr_owner = self.env["hr.employee"].search(args)

        if hr_owner.parent_id == hr_approver:
            return True

        raise AccessError(
            "You cannot approve this quote, because you are not"
            " set as %s's manager in the system"
            % hr_owner.user_id.name)

    def notify_availability_check(self):

        self.write({'state': 'need_availability_check'})

        template = self.env.ref('xpr_sale_process.quotation_availability_notify_mail')

        values = self.env['email.template'].generate_email(
            template.id, self.id)

        destination_ids = set([
            u.partner_id.id for u in self.category.approval_group.users if u.partner_id])

        values['recipient_ids'] = [(4, pid) for pid in destination_ids]

        self.env['mail.mail'].create(values)

    def notify_manager_approval(self):
        self.write({'state': 'need_manager_approval'})

        args = [("user_id", "=", self.user_id.id)]
        hr_owner = self.env["hr.employee"].search(args)

        if not hr_owner:
            return

        template = self.env.ref('xpr_sale_process.quotation_manager_approval_mail')

        values = self.env['email.template'].generate_email(
            template.id, self.id)

        values['recipient_ids'] = [(4, hr_owner.user_id.partner_id.id)]

        self.env['mail.mail'].create(values)

    def notify_manager_approval_interrupt(self):

        template = self.env.ref('xpr_sale_process.quotation_availability_reopen_mail')

        values = self.env['email.template'].generate_email(
            template.id, self.id)

        destination_ids = set([
            u.partner_id.id for u in self.category.approval_group.users if u.partner_id])

        values['recipient_ids'] = [(4, pid) for pid in destination_ids]

        self.env['mail.mail'].create(values)

    # Template helper
    @property
    def form_url(self):

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        return "/web#id={1}&view_type=form&model=sale.order".format(
            base_url,
            self.id)


class ProductCategory(models.Model):
    _inherit = "product.category"

    approval_group = fields.Many2one(
        'res.groups',
        'Approval Group',
        help="Group of users that must approve products of this category")


class LeadMixin(object):
    """
    Adds a solution in leads. Necessary to create quotes
    """

    _inherit = "crm.lead"

    @api.onchange('category')
    def _changed_category(self):
        return {
            'domain':
            {'solution': [('category', '=', self[0].category.id)]}
        }

    @api.onchange('solution')
    def _changed_solution(self):
        for lead in self:
            lead.name = lead.solution.name
            lead.category = lead.solution.category

    category = fields.Many2one('product.category')
    solution = fields.Many2one('xpr_solution_builder.solution')


class Lead(models.Model, LeadMixin):
    _inherit = "crm.lead"

#     @api.depends('probability', 'planned_revenue')
#     def _get_funnel_score(self):
#         # Calculates revenue esperance (not estimation)
#         for lead in self:
#             lead.funnel_score = lead.probability * lead.planned_revenue / 100

#     funnel_score = fields.Float(
#         'Funnel Score',
#         compute=_get_funnel_score,
#         store=True)


class LeadMakeSale(models.Model, LeadMixin):
    _inherit = "crm.make.sale"

    @api.model
    def _selectCategory(self):
        """
        This function gets default value for category field.
        @param self: The object pointer
        @return: default value of category field.
        """

        context = self.env.context

        if context is None:
            context = {}

        lead_obj = self.env['crm.lead']
        active_id = context.get('active_id')

        if not active_id:
            return None

        lead = lead_obj.browse(active_id)
        return lead.category if lead else None

    @api.model
    def _selectSolution(self):
        """
        This function gets default value for solution field.
        @param self: The object pointer
        @return: default value of solution field.
        """

        context = self.env.context

        if context is None:
            context = {}

        lead_obj = self.env['crm.lead']
        active_id = context.get('active_id')

        if not active_id:
            return None

        lead = lead_obj.browse(active_id)
        return lead.solution if lead else None

    _defaults = {
        'category': _selectCategory,
        'solution': _selectSolution,
        'close': True,
    }
