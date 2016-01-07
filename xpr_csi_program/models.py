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

    # Extend parnter onchange method
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(SaleOrder, self).onchange_partner_id(cr, uid, ids, part, context)
        res.update({'domain': {'csi_contact': [('parent_id', '=', part)]}})

        return res

    @api.onchange('solution')
    def _reset_csi_contact(self):
        self.csi_contact = None

    csi_contact = fields.Many2one('res.partner', 'CSI Contact Sales')
