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
            # ('progress', 'Sales Order'),
            # ('shipping_except', 'Shipping Exception'),
            # ('invoice_except', 'Invoice Exception'),
            ('waiting_date', 'Waiting Schedule'),
            ('need_manager_approval', 'Need Manager Approval'),
            ('manager_approved', 'Manager Approved'),
            ('manager_not_approved', 'Manager Declined'),
            ('contract_not_presented', 'Not Presented to Customer'),
            ('contract_approved', 'Approved by Customer'),
            ('contract_not_approved', 'Not Approved by Customer'),
            ('need_availability_check', 'Need Availability Check'),
            # ('sent', 'Quotation Sent'),
            ('production', 'Prod'),
            ('manual', 'Sale to Invoice'),
            ('cancel', 'Cancelled'),
            ('lost', 'Lost'),
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
            if line.discount_money:
                return True

        return False

    @api.multi
    def action_require_availability_check(self):
        """
        Starts Wizard to get rep or adteam notes
        """
        for order in self:
            return {
                'name': (
                    order.state != "need_availability_check" and 'Availability approval request' or
                    'Availability quotation refused'
                ),
                'type': 'ir.actions.act_window',
                'res_model': 'xpr_sale_process.availability_message',
                'views': [[False, "form"]],
                'target': 'new',
                'view_id': self.env.ref('xpr_sale_process.view_availability_check_message').id,
                'context': {'order_id': self.id}
            }

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
        or if as a sales manager and leader of the users sales team.
        An AccessError exception is
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

        try:
            if self.env.user.id == self.user_id.partner_id.section_id.user_id.id:
                return True
        except:
            raise AccessError(
                "You cannot approve this quote, because you are not"
                " set as %s's sales team leader in the system"
                % self.user_id.name)

    def notify_manager_approval(self):
        """
        Notify team manager of current order salesman for discount approval
        """
        self.write({'state': 'need_manager_approval'})

        salesman = self.user_id.partner_id

        if not salesman:
            # No salesman. No team.
            return

        team = salesman.section_id

        if not team:
            # No team, no team leader.
            return

        if team.user_id.id == self.env.user.id:
            # User is actually the leader. No need to auto notify.
            return

        template = self.env.ref('xpr_sale_process.quotation_manager_approval_mail')

        values = self.env['email.template'].generate_email(
            template.id, self.id)

        values['recipient_ids'] = [(4, team.user_id.partner_id.id)]

        self.env['mail.mail'].create(values)

    def notify_manager_approval_interrupt(self):

        template = self.env.ref('xpr_sale_process.quotation_availability_reopen_mail')

        values = self.env['email.template'].generate_email(
            template.id, self.id)

        destination_ids = set([
            u.partner_id.id for u in self.category.approval_group.users if u.partner_id])

        values['recipient_ids'] = [(4, pid) for pid in destination_ids]

        self.env['mail.mail'].create(values)

    def approve_contract(self):
        self.write({'state': 'contract_approved'})

    # Template helper
    @property
    def form_url(self):
        return "/web#id={0}&view_type=form&model=sale.order".format(
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


class LeadMakeSale(models.TransientModel, LeadMixin):
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


class AvailabilityMessage(models.TransientModel):

    _name = 'xpr_sale_process.availability_message'

    def _default_order(self):
        return self.env['sale.order'].browse(self._context.get('order_id'))

    def _for_approval(self):
        return self.env['sale.order'].browse(
            self._context.get('order_id')).state != "need_availability_check"

    @api.one
    def notify_availability_check(self):

        order = self.order_id

        order.write({'state': 'need_availability_check'})

        template = self.env.ref('xpr_sale_process.quotation_availability_notify_mail')

        values = self.env['email.template'].with_context(message=self.message).generate_email(
            template.id, order.id)

        destination_ids = set([
            u.partner_id.id
            for u in order.category.approval_group.users
            if u.partner_id
        ])

        values['recipient_ids'] = [(4, pid) for pid in destination_ids]

        self.env['mail.mail'].create(values)

    @api.one
    def notify_availability_refused(self):

        from openerp import workflow

        order = self.order_id

        template = self.env.ref('xpr_sale_process.quotation_availability_refused')

        values = self.env['email.template'].with_context(message=self.message).generate_email(
            template.id, order.id)

        values['email_from'] = self.env.user.email

        self.env['mail.mail'].create(values)

        workflow.trg_validate(
            self.env.uid,
            'sale.order', order.id,
            'sig_availability_not_checked',
            self.env.cr)

    order_id = fields.Many2one('sale.order', default=_default_order)
    for_approval = fields.Boolean(default=_for_approval)
    message = fields.Text("Message")
