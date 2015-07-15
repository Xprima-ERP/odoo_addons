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

from openerp import models, fields, api

class product_product(models.Model):
    _inherit = "product.product"
    
    # Deprecated
    # x_sf_id = fields.Char('Salesforce ID', size=18, select=True)
    # x_region = fields.Char('Region', size=254)

    x_description_fr = fields.Char('Description FR', size=254)
    x_name_fr = fields.Char('Name FR', size=254)
    x_one_time_payment = fields.Boolean('One Time Payment')

    # x_family = Reference to a 'x_family' attribute in OpenERP.
    # Used for reports.
    # Good chance will be replaced with other fields

    # x_family attribute records have simply a name, which can be one of these:
    # Visibility
    # Advertising - One time
    # Advertising
    # Training
    # Package option - One time
    # Package option
    # Package
    # Monthly
    # One Time



# Not using pricelists anymore
# class product_pricelist(osv.osv):
#     _inherit = "product.pricelist"
#     _columns = {
#         'x_sf_id': fields.char('Salesforce ID', size=18, select=True),
#         'x_description': fields.char('Description', size=254),
#     }
