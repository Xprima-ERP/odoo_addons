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

    @api.onchange('partner_id')
    def _change_csi_contact_domain(self):
        return {'domain': {'csi_contact': [('parent_id', '=', self.partner_id)]}}

    @api.onchange('solution')
    def _reset_csi_contact(self):
        self.csi_contact = None

    csi_contact = fields.Many2one('res.partner', 'CSI Contact Sales')
