# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


class Solution(models.Model):
    """ Solution model that regroup products together"""

    _name = 'xpr_solution_builder.solution'

    name = fields.Char(required=True)
    description = fields.Char(required=True)
    list_price = fields.Float(string='Solution Price', digits=(6,2))

    products = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_mandatory_product_rel',
        string='Mandatory Products')

    options = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_optional_product_rel',
        string='Optional Products')


class SalesOrder(models.Model):
    """ Override of sale.order to add solution field"""

    _inherit = "sale.order"

    @api.depends('order_line')
    def _get_line_products(self):

        for record in self:
            record.order_line_products = self.env['sale.order.line']
            for line in record.order_line:
                # Do not include integration line
                if line.solution_part == 1:
                    record.order_line_products += line

    @api.depends('order_line')
    def _get_line_options(self):

        for record in self:
            record.order_line_options = self.env['sale.order.line']
            for line in record.order_line:
                if line.solution_part == 2:
                    record.order_line_options += line

    @api.depends('order_line')
    def _get_amount_products(self):
        for order in self:
            order.amount_products_untaxed = sum([
                line.price_unit * line.product_uom_qty * (1.0 - line.discount / 100.0)
                for line in order.order_line
                if line.solution_part in [1, 3]
            ])

    @api.depends('order_line')
    def _get_amount_options(self):
        for order in self:
            order.amount_options_untaxed = sum([
                line.price_unit * line.product_uom_qty
                for line in order.order_line
                if line.solution_part == 2
            ])

    solution = fields.Many2one('xpr_solution_builder.solution', string='Solution')
    rebate = fields.Float(string='Rebate', digits=(6,2))

    order_line_products = fields.One2many('sale.order.line', compute=_get_line_products)
    order_line_options = fields.One2many('sale.order.line', compute=_get_line_options)
    amount_products_untaxed = fields.Float(string='Products', digits=(6,2), compute=_get_amount_products)
    amount_options_untaxed = fields.Float(string='Options', digits=(6,2), compute=_get_amount_options)

    def _apply_solution(self, order):

        discount_rate = self._get_discount_rate(order)

        # override order lines

        order.order_line = self.env['sale.order.line']

        delta_price = order.solution.list_price
        sequence = 0

        for product in order.solution.products:
            sequence += 10
            delta_price -= product.list_price

            order.order_line += order.order_line.new(dict(
                order_id=order.id,
                product_id=product.id,
                name=product.name,
                product_uom_qty=1.0,
                price_unit=product.list_price,
                solution_part=1,
                discount=discount_rate,
                product_uom=product.uom_id,
                sequence=sequence,
                state=order.state,
            ))

        sequence += 10
        order.order_line += order.order_line.new(dict(
                order_id=order.id,
                name="Solution integration",
                price_unit=delta_price,
                solution_part=3,
                discount=discount_rate,
                sequence=sequence,
                state=order.state,
            ))

    def _get_discount_rate(self, order):

        if order.solution:
            price = sum([
                line.product_id.list_price * line.product_uom_qty
                for line in order.order_line
                if line.solution_part in [1,3]
            ])

            # price == order.list_price
            
            if price:
                return 100.0 * order.rebate / max(price, order.rebate)

        return 0.0

    def _apply_rebate(self, order):

        discount_rate = self._get_discount_rate(order)

        for line in order.order_line:
            if line.solution_part in [1,3]:
                line.discount = discount_rate


    @api.onchange('solution')
    def onchange_solution(self):

        for order in self:
            self._apply_solution(order)

        return {}

    @api.onchange('rebate')
    def onchange_rebate(self):
        for order in self:
            self._apply_rebate(order)

        return {}


class SalesOrderLine(models.Model):
    """ Override of sale.order to add solution field"""

    _inherit = "sale.order.line"

    # 0 Don't care (not solution)
    # 1 mandatory line
    # 2 optional line
    # 3 price correction line
    solution_part = fields.Integer() 

class SolutionConfigurator(models.TransientModel):

    """ 
        Solution Configurator wizard.

        Loaded to select optional product from related solution
        Updates order lines of sales order whenever
        products are added or removed.
    """

    _name = 'xpr_solution_builder.solution_configurator'

    def _default_order(self):
        return self.env['sale.order'].browse(self._context.get('order_id'))

    def _default_solution(self):
        return self.env['xpr_solution_builder.solution'].browse(self._context.get('solution_id'))

    def _default_products(self):
        order = self._default_order()
        solution = self._default_solution()

        if not order or not solution:
            # Should not get here.
            return []

        # Return optional products that are at least one order line

        options = set([item.id for item in solution.options])
        products = set([line.product_id.id for line in order.order_line])

        return sorted(options & products)

    order = fields.Many2one(
        'sale.order',
        string='Order',
        required=True,
        default=_default_order)

    solution = fields.Many2one(
        'xpr_solution_builder.solution',
        string='Solution',
        required=True,
        default=_default_solution)

    products = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_configurator_product_rel',
        string='Product',
        default=_default_products)

    # This field is a hack for widget display needs
    dummy = fields.Boolean()

    @api.one
    def set_products(self):

        options = set([item.id for item in self.solution.options])

        selected_products = set([product.id for product in self.products])
        products_in_order = set()

        removed_lines = []

        for line in self.order.order_line:
            if line.solution_part != 2:
                continue

            if line.product_id.id not in options:
                continue

            products_in_order.add(line.product_id.id)

            if line.product_id.id in selected_products:
                continue

            # Optional product not selected anymore.
            # Delete line from order.
            removed_lines.append(line)

        # Delete lines of optinal products that are not selected anymore
        for line in removed_lines:
            line.unlink()

        line = self.env['sale.order.line']

        added_products = selected_products - products_in_order

        # Go through products again and insert lines for newly selected ones.
        for product in self.products:
            if product.id not in added_products:
                continue

            line.create(
                dict(
                    order_id=self.order.id,
                    product_id=product.id,
                    name=product.name,
                    product_uom_qty=1.0,
                    solution_part=2))

        return {}

    @api.onchange('dummy')
    def onchange_dummy(self):
        # dummy is used to force a refresh in the view
        return {}

    @api.onchange('solution')
    def onchange_solution(self):

        solution = self.solution

        if solution:
            solution = solution[0]

        if not solution:
            return []

        domain_ids = [item.id for item in solution.options]

        # Force a proper refresh of the products widget
        self.dummy = not self.dummy

        return {'domain': {'products': [('id', 'in', domain_ids)]}}
