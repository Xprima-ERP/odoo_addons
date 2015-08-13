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
    _inherit = "product.template"
    
    # Deprecated
    # x_sf_id = fields.Char('Salesforce ID', size=18, select=True)
    # x_region = fields.Char('Region', size=254)
    # x_description_fr = fields.Char('Description FR', size=254)
    # x_name_fr = fields.Char('Name FR', size=254)

    one_time_payment = fields.Boolean('One Time Payment')

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


class sale_order(models.Model):
    _inherit = "sale.order"

    def _get_one_time_total(self):
    
        for sale_order in self:
            sale_order.one_time_total = sum([line.price_subtotal for line in sale_order.order_line if line.product_id.one_time_payment])


    def _get_monthly_total(self):

        for sale_order in self:
            sale_order.monthly_total = sum([line.price_subtotal for line in sale_order.order_line if not line.product_id.one_time_payment])

    one_time_total = fields.Float(string='One Time Total', digits=(6,2), compute=_get_one_time_total)
    monthly_total = fields.Float(string='Monthly Total', digits=(6,2), compute=_get_monthly_total)
