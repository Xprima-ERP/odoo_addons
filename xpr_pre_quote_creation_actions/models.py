# -*- coding: utf-8 -*-

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
