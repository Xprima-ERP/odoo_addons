# -*- coding: utf-8 -*-

from osv import osv, fields


class Partner(osv.Model):
    _name = 'res.partner'
    _columns = {
                'csi_contact_am': fields.many2one('res.partner', 'CSI Contact A.M.'),
               }
    _inherit = 'res.partner'

Partner()
