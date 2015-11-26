# -*- coding: utf-8 -*-

# from osv import osv, fields


# class Partner(osv.Model):
#     _name = 'res.partner'
#     _columns = {
#                 'csi_contact_am': fields.many2one('res.partner', 'CSI Contact A.M.'),
#                }
#     _inherit = 'res.partner'

# class SaleOrder(osv.Model):
#     _name = 'sale.order'
#     _columns = {
#                 'csi_contact': fields.many2one('res.partner', 'CSI Contact Sales'),
#                 'partner_invoice_id': fields.many2one('res.partner',
#                                                       'Invoice Address',
#                                                       readonly=True,
#                                                       required=False,
#                                                       states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
#                                                       help="Invoice address for current sales order."),
#                 'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address',
#                                                        readonly=True,
#                                                        required=False,
#                                                        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
#                                                        help="Delivery address for current sales order."),
#                }
#     _inherit = 'sale.order'

#     def on_change_partner_id(self, cr, uid, ids, partner_id, context):
#         return {'domain': {'csi_contact': [('parent_id', '=', partner_id)]}}

