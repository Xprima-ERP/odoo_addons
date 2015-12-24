# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


class Partner(models.Model):
    #_name = 'res.partner'
    _inherit = 'res.partner'

    csi_contact_am = fields.Many2one('res.partner', 'CSI Contact A.M.')


class SaleOrder(models.Model):
    #_name = 'sale.order'
    _inherit = 'sale.order'

    csi_contact = fields.Many2one('res.partner', 'CSI Contact Sales')

    # Form helper

    def on_change_partner_id(self, cr, uid, ids, partner_id, context):
        return {'domain': {'csi_contact': [('parent_id', '=', partner_id)]}}
