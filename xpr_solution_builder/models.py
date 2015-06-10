# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


class Solution(models.Model):
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

    """Solution Configurator wizard"""

    _name = 'xpr_solution_builder.solution_configurator'

    def _default_order(self):
        return self.env['sale.order'].browse(self._context.get('order_id'))

    def _default_solution(self):
        return self.env['xpr_solution_builder.solution'].browse(self._context.get('solution_id'))

    order = fields.Many2one('sale.order',string='Order', required=True, default=_default_order)
    solution = fields.Many2one('xpr_solution_builder.solution',string='Solution',required=True, default=_default_solution)
    products = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_configurator_product_rel',
        string='Product')

    @api.one
    def set_products(self):
       
        line = self.env['sale.order.line']

        for product in self.products:
            line.create(
                dict(
                    order_id=self.order.id,
                    product_id=product.id,
                    name=product.name,
                    product_uom_qty=1.0))

        return {}

    @api.one
    @api.onchange('solution_id')
    def onchange_solution(self):

        domain_ids = []

        solution = self.solution

        if solution:
            domain_ids = [item.id for item in solution.options]

        return {'domain': {'products': [('id', 'in', domain_ids)]}}
