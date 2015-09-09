# -*- coding: utf-8 -*-

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class Solution(models.Model):
    """ Solution model that regroup products together"""

    _name = 'xpr_solution_builder.solution'

    name = fields.Char(required=True)
    description = fields.Char(required=True)
    list_price = fields.Float(string='Solution Price', digits=(6, 2))

    products = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_mandatory_product_rel',
        string='Mandatory Products')

    products_extra = fields.One2many(
        'xpr_solution_builder.solution.line',
        'solution',
        string='Mandatory Product Count')

    options = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_optional_product_rel',
        string='Optional Products')

    options_extra = fields.One2many(
        'xpr_solution_builder.solution.option',
        'solution',
        string='Optional Product configuration')

    @api.onchange('products')
    def _update_product_extras(self):
        """
        Takes care of synching the product_extras with products.
        """

        for solution in self:
            new_set = set(solution.products.ids)
            old_set = set([ex.product.id for ex in solution.products_extra])

            if new_set == old_set:
                continue

            extras = self.env['xpr_solution_builder.solution.line']

            # Keep common records
            for ex in solution.products_extra:
                if ex.product.id in new_set:
                    extras += ex

            # Add new ones
            for product in solution.products:
                if product.id not in new_set - old_set:
                    continue

                ex = extras.new()
                ex.solution += solution
                ex.product += product
                ex.times = 1

                extras += ex

            # Assign new recordset
            solution.products_extra = extras

    @api.onchange('options')
    def _update_option_extras(self):
        """
        Takes care of synching the options_extras with products.
        """

        for solution in self:
            new_set = set(solution.options.ids)
            old_set = set([ex.product.id for ex in solution.options_extra])

            if new_set == old_set:
                continue

            extras = self.env['xpr_solution_builder.solution.option']

            # Keep common records
            for ex in solution.options_extra:
                if ex.product.id in new_set:
                    extras += ex

            # Add new ones
            for product in solution.options:
                if product.id not in new_set - old_set:
                    continue

                ex = extras.new()
                ex.solution += solution
                ex.product += product
                ex.selected_default = False
                ex.sticky = False

                extras += ex

            # Assign new recordset
            solution.options_extra = extras


class SolutionProductLine(models.Model):
    """
    Solution line model. Permits additional info on
    relation between solution line and mandatory product.
    This model is in parallel of the products relation in order to add
    additional parameters while using the same wizard as a many2many relation
    """

    _name = 'xpr_solution_builder.solution.line'
    #_table = 'xpr_solution_builder_solution_mandatory_product_rel'

    times = fields.Integer(default=1, string='Quantity')

    solution = fields.Many2one(
        'xpr_solution_builder.solution',
        string='Solution',
        readonly=True)

    # Should always contain exactly 1 record.
    product = fields.Many2one(
        'product.product', 'Product', readonly=True)


class SolutionOptionLine(models.Model):
    """
    Solution optional line model. Permits additional info on
    relation between solution line and optional products.
    This model is in parallel of the options relation in order to add
    additional parameters while using the same wizard as a many2many relation
    """

    _name = 'xpr_solution_builder.solution.option'
    #_table = 'xpr_solution_builder_solution_optional_product_rel'

    selected_default = fields.Boolean(string='Auto Select')
    sticky = fields.Boolean(string='Cannot be removed')

    solution = fields.Many2one(
        'xpr_solution_builder.solution',
        string='Solution',
        readonly=True)

    # Should always contain exactly 1 record.
    product = fields.Many2one('product.product', 'Product', readonly=True)


class SalesOrder(models.Model):
    """
    Override of sale.order to add thse fields:
    - solution
    - solution discount

    Permits to:
    - Apply solution discount on mandatory item lines
    - Calculate separate totals for mandatory and optional lines.
    """

    _inherit = "sale.order"

    def onchange_pricelist_id(
        self, cr, uid, ids, pricelist_id, return_lines, context={}
    ):
        # Override default behavior that fires useless warning.
        # Pricelists are not used.

        res = super(SalesOrder, self).onchange_pricelist_id(
            cr, uid, ids, pricelist_id, return_lines, context)

        if 'warning' in res:
            res.pop('warning')

        return res

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

    def _get_line_amount(self, line):
        line_base = line.price_unit * line.product_uom_qty
        return line_base - line.discount_money

    @api.depends('order_line')
    def _get_amount_products(self):

        for order in self:
            order.amount_products_untaxed = sum([
                self._get_line_amount(line)
                for line in order.order_line if line.solution_part != 2
            ])

    @api.depends('order_line')
    def _get_amount_options(self):

        for order in self:
            order.amount_options_untaxed = sum([
                self._get_line_amount(line)
                for line in order.order_line if line.solution_part == 2
            ])

    solution = fields.Many2one(
        'xpr_solution_builder.solution', string='Solution', required=True)

    solution_discount = fields.Float(
        string='Solution Discount ($)', digits=(6, 2))

    order_line_products = fields.One2many(
        'sale.order.line', compute=_get_line_products)

    order_line_options = fields.One2many(
        'sale.order.line', compute=_get_line_options)

    amount_products_untaxed = fields.Float(
        string='Solution', digits=(6, 2), compute=_get_amount_products)

    amount_options_untaxed = fields.Float(
        string='Options', digits=(6, 2), compute=_get_amount_options)

    def _apply_solution(self, order):
        """
            Builds sales order using solution as template.
        """

        quantities = dict([
            (ex.product.id, ex.times) for ex in order.solution.products_extra
        ])

        # override order lines

        order.order_line = self.env['sale.order.line']

        delta_price = order.solution.list_price
        sequence = 0
        mandatory_products = list(order.solution.products) + [
            item.product for item in self.solution.options_extra
            if item.sticky
        ]

        for product in mandatory_products:

            sequence += 10
            qty = quantities.get(product.id, 1.0)
            delta_price -= product.list_price * qty

            order.order_line += order.order_line.new(dict(
                order_id=order.id,
                product_id=product.id,
                name=product.description_sale or ' ',
                product_uom_qty=qty,
                price_unit=product.list_price,
                solution_part=1,
                product_uom=product.uom_id,
                sequence=sequence,
                state=order.state,
            ))

        if delta_price != 0:
            unit = self.env['product.uom'].search(
                [('name', '=', 'Unit(s)'), ('factor', '=', '1')])[0]

            sequence += 10
            order.order_line += order.order_line.new(dict(
                order_id=order.id,
                name="Solution integration",
                price_unit=delta_price,
                solution_part=3,
                product_uom_qty=1,
                product_uom=unit.id,
                sequence=sequence,
                state=order.state,
            ))

    def _apply_solution_discount(self, order):

        solution_discount_line = None

        lines = self.env['sale.order.line']

        for line in order.order_line:
            if line.solution_part != 4:
                lines += line
                continue

        solution_discount = -min(
            order.solution.list_price, order.solution_discount)

        if solution_discount != 0:
            unit = self.env['product.uom'].search(
                [('name', '=', 'Unit(s)'), ('factor', '=', '1')])[0]

            lines += order.order_line.new(dict(
                order_id=order.id,
                name="Solution discount",
                price_unit=solution_discount,
                solution_part=4,
                state=order.state,
                product_uom_qty=1,
                product_uom=unit.id,
            ))

        order.order_line = lines

    @api.onchange('solution')
    def onchange_solution(self):

        for order in self:
            self._apply_solution(order)

        return {}

    @api.onchange('solution_discount')
    def onchange_solution_discount(self):
        for order in self:
            self._apply_solution_discount(order)

        return {}

    @api.multi
    def sale_solution_option_action(self):
        for order in self:
            # manage only one order

            if not order.solution:
                return {}

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'xpr_solution_builder.solution_configurator',
                'views': [[False, "form"]],
                'target': 'new',
                'view_id': 'view_solution_configurator_wizard',
                'context': {'order_id': order.id}
            }


class SalesOrderLine(models.Model):
    """ Override of sale.order to add solution field"""

    _inherit = "sale.order.line"

    @api.onchange('discount_money')
    def onchange_discount_money(self):
        """
        Permit money discounts on optional lines only.
        Update discount for consistency and to trigger update events.
        """

        for line in self:
            if (
                line.solution_part == 2
                and line.price_unit and line.product_uom_qty
            ):
                line.discount_money = max(
                    0,
                    min(
                        line.discount_money,
                        line.product_uom_qty * line.price_unit))

                line.discount = (
                    100.0 * line.discount_money
                    / line.product_uom_qty / line.price_unit
                )
            else:
                line.discount_money = 0

        return {}

    @api.onchange('price_unit', 'product_uom_qty', 'discount_money')
    def _amount_line(self):
        """
        Override from sales order line in sale module
        Disables taxes and replaces discount
        """

        for line in self:
            amount = line.price_unit * line.product_uom_qty
            if line.discount_money > 0:
                # Discounts should never permit to go negative.
                line.price_subtotal = max(
                    0,
                    amount - line.discount_money)
                continue

            # Subtotal may already be negative (with discount == 0)
            line.price_subtotal = amount

    # 0 Don't care (not solution)
    # 1 mandatory line
    # 2 optional line
    # 3 price correction line for mandatory products
    # 4 solution discount

    solution_part = fields.Integer(default=0)
    discount_money = fields.Float(
        string='Discount ($)', digits=(6, 2), default=0)

    # Override required to redirect to new compute function.
    # Otherwise, function pointer still points to overriden version.
    price_subtotal = fields.Float(
        digits=(6, 2),
        string='Subtotal',
        digits_compute=dp.get_precision('Account'),
        compute=_amount_line)


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
        return self._default_order().solution

    def _default_products(self):
        order = self._default_order()
        solution = self._default_solution()

        if not order or not solution:
            # Should not get here.
            return []

        # Return optional products that are at least one order line

        options = set([item.id for item in solution.options])
        products = set([line.product_id.id for line in order.order_line])
        stickies = set([
            item.product.id for item in solution.options_extra if item.sticky
        ])

        defaults = (options & products) | stickies

        if not defaults - stickies:
            # No lines yet in order. Propose default selected products.
            defaults = options & set([
                item.product.id for item in solution.options_extra
                if item.selected_default or item.sticky
            ])

        return sorted(defaults)

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

        selected_products = set([
            product.id for product in self.products
        ]) - set([
            item.product.id for item in self.solution.options_extra
            if item.sticky
        ])

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
                    name=product.description_sale or ' ',
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
