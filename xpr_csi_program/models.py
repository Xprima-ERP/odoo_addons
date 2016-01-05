# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


# class Partner(models.Model):
#     #_name = 'res.partner'
#     _inherit = 'res.partner'

#     csi_contact_am = fields.Many2one('res.partner', 'CSI Contact A.M.')


class SaleOrder(models.Model):
    #_name = 'sale.order'
    _inherit = 'sale.order'

    csi_contact = fields.Many2one('res.partner', 'CSI Contact Sales')
