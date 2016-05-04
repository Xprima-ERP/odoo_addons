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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Deprecated
    # x_sf_id = fields.Char('Salesforce ID', size=18, select=True)
    # x_region = fields.Char('Region', size=254)
    # x_description_fr = fields.Char('Description FR', size=254)
    # x_name_fr = fields.Char('Name FR', size=254)
    # x_family = Reference in OpenERP. Replaced by product category.

    one_time_payment = fields.Boolean('One Time Payment')

    # Different field than categ_id.
    # There is much logic attached to that other field.
    # Furthermore, this one is optional.
    categ_term = fields.Many2one(
        'product.category',
        'Category',
        domain="[('type','=','normal')]",
        help="Select category for the current product")

    # Override parent field. Made readonly. Set code in variants
    default_code = fields.Char(
        related="product_variant_ids.default_code",
        string="Internal Reference",
        readonly=True)


class Product(models.Model):
    """
    All variants of same product without any code get the same reference number.
    """
    _inherit = "product.product"

    @api.multi
    def write(self, vals):

        res = super(Product, self).write(vals)

        if 'default_code' not in vals or not res:
            return res

        # In theory, products in recordset could
        # come from different templates. There is typically only one.
        templates = [p.product_tmpl_id.id for p in self]

        # Propagate default code to sibling variants.

        default_code = vals['default_code']

        siblings = self.search([
            ('product_tmpl_id', 'in', templates),
            ('default_code', '!=', default_code), # Avoid recursive calls.
            ('default_code', 'in', ['', None]), # Set codes only for unset siblings.
        ])

        if siblings:
            siblings.write({'default_code': default_code})

        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_one_time_total(self):

        for sale_order in self:
            sale_order.one_time_total = sum([
                line.price_subtotal for line in sale_order.order_line
                if line.product_id.one_time_payment
            ])

    def _get_monthly_total(self):

        for sale_order in self:
            sale_order.monthly_total = sum([
                line.price_unit - line.discount_money for line in sale_order.order_line
                if not line.product_id.one_time_payment
            ])

    one_time_total = fields.Float(
        string='One Time Total', digits=(6, 2), compute=_get_one_time_total)

    monthly_total = fields.Float(
        string='Monthly Total', digits=(6, 2), compute=_get_monthly_total)
