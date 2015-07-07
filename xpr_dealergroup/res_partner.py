# -*- encoding: utf-8 -*-
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from openerp.osv import osv, fields


class res_partner_category_cert(osv.osv):
    _description = 'Partner Categories Certifications'
    _name = 'res.partner.category.certification'
    _columns = {
        'name': fields.char('Certification Name', required=True, size=64,
                            translate=True),
        'description': fields.text('Description', translate=True),
        'automatic': fields.boolean('Automatic'),
    }
    _defaults = {
        'automatic': False,
    }


class res_partner_category(osv.osv):
    _name = 'res.partner.category'
    _inherit = "res.partner.category"

    _columns = {
        'certification': fields.many2many(
            'res.partner.category.certification',
            'res_partner_category_certification_rel',
            'category_id',
            'certification_id',
            'Certification'),
        'x_sf_id': fields.char('Salesforce ID', size=18, select=True),
        'x_salesperson': fields.many2one('res.users','Salesperson'),
        'x_dealergroup': fields.char('Dealergroup', size=254),
        'x_description_fr': fields.char('Description FR', size=254),
    }
