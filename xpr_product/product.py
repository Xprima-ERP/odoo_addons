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


class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'x_sf_id': fields.char('Salesforce ID', size=18, select=True),
        'x_region': fields.char('Region', size=254),
        'x_description_fr': fields.char('Description FR', size=254),
        'x_name_fr': fields.char('Name FR', size=254),
    }


class product_pricelist(osv.osv):
    _inherit = "product.pricelist"
    _columns = {
        'x_sf_id': fields.char('Salesforce ID', size=18, select=True),
        'x_description': fields.char('Description', size=254),
    }
