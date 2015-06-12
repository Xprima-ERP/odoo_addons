# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


class Solution(models.Model):
    """ Solution model that regroup products together"""

    _name = 'xpr_solution_builder.solution'

    name = fields.Char(required=True)
    description = fields.Char(required=True)
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

    solution = fields.Many2one('xpr_solution_builder.solution', string='Solution')

    #TODO: Use on_change('solution') and @constrains

    # Traditional ORM
    def create(self, cr, user, vals, context=None):
        record_id = super(SalesOrder, self).create(cr, user, vals, context)

        if not record_id:
            return record_id

        self.complete_line_items(cr, user, record_id, context)
        return record_id

    def write(self, cr, user, ids, vals, context=None):

        result = super(SalesOrder, self).write(cr, user, ids, vals, context)

        if not result:
            return result

        for record_id in ids:
            self.complete_line_items(cr, user, record_id, context)

        # result = True or Exception is raised

        return result

    def complete_line_items(self, cr, user, record_id, context):

        order = self.browse(cr, user, record_id, context=context)
        if not order.solution:
            # No solution selected. No validation.
            return

        solution = self.pool.get(
            Solution._name
        ).browse(
            cr, user, order.solution.id,  context=context
        )

        mandatory_ids = set(solution.products.ids)
        all_ids = mandatory_ids | set(solution.options.ids)

        order_products = set([line.product_id.id for line in order.order_line])

        if order_products - all_ids:
            raise SalesOrder.ValidateError('Products not part of solution')

        # Add missing line items from mandatory products

        missing_products = self.pool.get(
            'product.product'
        ).browse(
            cr, user, list(mandatory_ids - order_products), context=context)

        order_line_obj = self.pool.get(order.order_line._name)

        for product in missing_products:
            order_line_obj.create(
                cr,
                user,
                dict(
                    order_id=order.id,
                    product_id=product.id,
                    name=product.name,
                    product_uom_qty=1.0),
                context=context)


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
            if line.product_id.id not in options:
                continue

            products_in_order.add(line.product_id.id)

            if line.product_id.id in selected_products:
                continue

            # Optional prouct not selected anymore.
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
                    product_uom_qty=1.0))

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
