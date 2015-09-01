# -*- coding: utf-8 -*-

from openerp.exceptions import AccessError
from openerp import models, fields


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = "sale.order"

    state = fields.Selection(
        [
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ('need_manager_approval', 'Need Manager Approval'),
            ('manager_approved', 'Manager Approved'),
            ('manager_not_approved', 'Manager Declined'),
            ('contract_not_presented', 'Not Presented to Customer'),
            ('contract_approved', 'Approved by Customer'),
            ('contract_not_approved', 'Not Approved by Customer'),
            ('need_availability_check', 'Need Availability Check'),
        ],
        'Status',
        readonly=True,
        copy=False,
        help="Gives the status of the quotation or sales order.\
        \nThe exception status is automatically set when a \
        cancel operation occurs in the invoice validation (Invoice Exception) \
        or in the picking list process (Shipping Exception).\nThe \
        'Waiting Schedule' status is set when the invoice is confirmed\
        but waiting for the scheduler to run on the order date.",
        select=True
    )

    order_line = fields.One2many(
        'sale.order.line',
        'order_id',
        'Order Lines',
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'manager_not_approved': [('readonly', False)],
            'contract_not_approved': [('readonly', False)],
            'sent': [('readonly', False)]},
        copy=True
    )

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
        for line in self.order_line:

            if not line.product_id:
                continue

            category = line.product_id.categ_term

            if not category:
                continue

            if category.approval_group:
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

        raise AccessError("You cannot approve this quote, because you are not"
                          " set as %s's manager in the system"
                          % hr_owner.user_id.name)

    # api.one
    def notify_manager_approval(self):
        self.write({'state': 'need_manager_approval'})

        #args = [("user_id", "=", self.env.user.id)]
        #hr_approver = self.env["hr.employee"].search(args)
        args = [("user_id", "=", self.user_id.id)]
        hr_owner = self.env["hr.employee"].search(args)

        #hr_owner.parent_id != hr_approver:

        body = """<p>Vous avez &agrave; approuver le devis <b>{0}</b>.</p>
        """.format(self.name)

        self.env['mail.message'].create({
            'type': 'notification',
            #'author_id':
            'partner_ids': [(4, hr_owner.id)],
            'record_name': self.name,
            'model': 'sale.order',
            'subject': 'Devis &agrave; approuver: {0}'.format(self.name),
            'body': body,
            #'template':
            #'subtype_id':
        })


class ProductCategory(models.Model):
    _inherit = "product.category"

    approval_group = fields.Many2one(
        'res.groups',
        'Approval Group',
        help="Group of users that must approve products of this category")
