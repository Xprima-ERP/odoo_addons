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
        approval_needed = self._check_discount()
        if not approval_needed:
            approval_needed = self._check_product_approver_needed()
        return approval_needed

    def _check_discount(self):
        for line in self.order_line:
            if line.discount:
                return True
        return False

    def _check_product_approver_needed(self):
        for line in self.order_line:
            if line.product_id.approver_groups:
                return True
        return False

    def has_rights_to_approve(self):
        """
        Return True if the user triggering this method has the right to approve
        the associated quote. The user has the right if he is the manager of
        the salesperson associated to the quote. An AccessError exception is
        raised if approver doesn't have the rights so he gets a warning in
        the web interface.
        """
        args = [("user_id", "=", self.env.user.id)]
        hr_approver = self.env["hr.employee"].search(args)
        args = [("user_id", "=", self.user_id.id)]
        hr_owner = self.env["hr.employee"].search(args)

        if hr_owner.parent_id == hr_approver:
            return True
        raise AccessError("You cannot approve this quote, because you are not"
                          " set as %s's manager in the system"
                          % hr_owner.user_id.name)

    def check_product_availability_needed(self):
        """
        Return True if product availability check is required and False if not.
        """
        for order_line in self.order_line:
            if order_line.product_id.availability_groups:
                return True
        return False

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


class Product(models.Model):
    _name = 'product.template'
    _inherit = "product.template"

    approver_groups = fields.Many2many(
        comodel_name="res.groups",
        string="Approver Groups",
        relation="product_to_approver_group"
    )

    availability_groups = fields.Many2many(
        comodel_name="res.groups",
        string="Availability Groups",
        relation="product_to_availability_group",
        help="Ask person from this group for product availability",
    )
