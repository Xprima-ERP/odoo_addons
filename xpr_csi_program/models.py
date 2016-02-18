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

        if not res:
            # Juse in case
            res = {}

        if not 'domain' in res:
            res['domain'] = {}

        if not 'value' in res:
            res['value'] = {}

        res['domain'].update({'csi_contact': [('parent_id', '=', part)]})
        res['value'].update({'csi_contact': None})
        return res

    @api.onchange('solution')
    def _reset_csi_contact(self):
        self.csi_contact = None

    @api.onchange('csi_contact')
    def _validate_csi_contact(self):

        for order in self:
            if not order.csi_contact or order.csi_contact.email:
                # All is fine
                continue

            order.csi_contact = None
            return {
                'warning': {
                    'title': 'Error',
                    'message': "CSI contact must have an email. Set email of select another one."
                }
            }

    @api.depends('category')
    def _csi_in_program(self):
        for order in self:
            order.csi_in_program = (order.category == order.env.ref('xpr_product.website'))

    csi_contact = fields.Many2one('res.partner', 'CSI Contact Sales')
    csi_in_program = fields.Boolean(string='In CSI Program', store=True, compute=_csi_in_program)
