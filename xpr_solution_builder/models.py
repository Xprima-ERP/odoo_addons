# -*- coding: utf-8 -*-

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class Solution(models.Model):
    """ Solution model that regroup products together"""

    _name = 'xpr_solution_builder.solution'

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

    @api.depends('name', 'default_code')
    def _display_name(self):
        for solution in self:
            if solution.default_code:
                solution.display_name = '[{0}] {1}'.format(
                    solution.default_code, solution.name)
            else:
                solution.display_name = solution.name

    name = fields.Char(required=True, translate=True)

    display_name = fields.Char(compute=_display_name)

    description = fields.Char(required=True, translate=True)
    list_price = fields.Float(string='Solution Price', digits=(6, 2))

    default_code = fields.Char('Internal Reference')

    products = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_mandatory_product_rel',
        string='Mandatory Products')

    products_extra = fields.One2many(
        'xpr_solution_builder.solution.line',
        'solution',
        string='Mandatory Product Quantity')

    options = fields.Many2many(
        'product.product',
        'xpr_solution_builder_solution_optional_product_rel',
        string='Optional Products')

    options_extra = fields.One2many(
        'xpr_solution_builder.solution.option',
        'solution',
        string='Optional Product configuration')

    category = fields.Many2one(
        'product.category',
        string='Category')

    budget = fields.Float(
        string='Budget',
        help="If set, expected budget this solution is for",
        digits=(6, 2),
        default=0)


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
        ondelete='cascade',
        readonly=True)

    # Should always contain exactly 1 record.
    product = fields.Many2one(
        'product.product', 'Product', ondelete='cascade', readonly=True)


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
        ondelete='cascade',
        readonly=True)

    # Should always contain exactly 1 record.
    product = fields.Many2one('product.product', 'Product', ondelete='cascade', readonly=True)


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
            lines = self.env['sale.order.line']
            for line in record.order_line:
                if line.solution_part in [0, 1]:
                    lines += line

            record.order_line_products = lines

    @api.depends('order_line')
    def _get_line_options(self):

        for record in self:
            lines = self.env['sale.order.line']
            for line in record.order_line:
                if line.solution_part == 2:
                    lines += line

            record.order_line_options = lines

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

    @api.depends('order_line')
    def _get_amount_all_untaxed(self):

        for order in self:
            order.amount_all_untaxed = sum([
                self._get_line_amount(line)
                for line in order.order_line
            ])

    @api.depends('solution')
    def _get_category(self):
        for order in self:
            order.category = order.solution.category

    def order_line_report(self):
        """
        Line ordering for reports.
        This sorting function should be in the report parser.
        """

        sections = [0, 1, 2]
        return sorted(
            [line for line in self.order_line if line.solution_part in sections],
            key=lambda line: (
                sections.index(line.solution_part), line.sequence, line.name))

    @api.model
    def create(self, vals):
        if 'solution' not in vals and 'solution' in self.env.context:
            # Read solution from context.
            # Happens when opportunity is converted.

            vals['solution'] = self.env.context['solution']

        if 'order_line' in vals:
            # Let apply solution take care of this
            vals.pop('order_line')

        order = super(SalesOrder, self).create(vals)

        if 'solution' in vals and 'order_line' not in vals:
            # Happens when opportunity is converted.
            self._apply_solution(order)

        return order

    solution = fields.Many2one(
        'xpr_solution_builder.solution', string='Solution')

    # Deprecated. TODO: Remove this.
    solution_discount = fields.Float(
        string='Solution Discount ($)', digits=(6, 2))

    order_line_products = fields.One2many(
        'sale.order.line', readonly=1, compute=_get_line_products)

    order_line_options = fields.One2many(
        'sale.order.line', readonly=1, compute=_get_line_options)

    solution_price = fields.Float(
        string="Solution Price",
        readonly=True,
        related="solution.list_price")

    amount_products_untaxed = fields.Float(
        string='Solution',
        digits_compute=dp.get_precision('Account'),
        compute=_get_amount_products)

    amount_options_untaxed = fields.Float(
        string='Options',
        digits_compute=dp.get_precision('Account'),
        compute=_get_amount_options)

    category = fields.Many2one(
        'product.category',
        string='Category',
        compute=_get_category,
        store=True)

    # 'Overwrite' of parent field: amount_untaxed
    # Had to rename fiel to by pass parent functionality
    amount_all_untaxed = fields.Float(
        string='Untaxed Amount',
        digits_compute=dp.get_precision('Account'),
        compute=_get_amount_all_untaxed,
        #multi='sums',
        #track_visibility='always',
        help="The amount without tax.")

    @api.multi
    def apply_patch(self):

        unit = self.env.ref('product.product_uom_categ_unit')

        has_zero = False
        for order in self:

            order.category = order.solution.category

            for line in list(order.order_line):

                if line.solution_part == 0:
                    if not line.product_id:
                        # Apply solution discount to first zero with no product.
                        line.discount_money = order.solution_discount
                        line.name=order.solution.description or ' '

                    has_zero = True

                if line.solution_part not in [0, 1, 2]:
                    line.unlink()
                    continue

                if line.solution_part == 1:
                    line.price_unit = 0

                # Reinit display name

            if order.solution.default_code and not has_zero:
                order.order_line += order.order_line.new(dict(
                    order_id=order,
                    #product_id
                    name=order.solution.description or ' ',
                    price_unit=order.solution.list_price,
                    solution_part=0,
                    product_uom_qty=1,
                    product_uom=unit.id,
                    sequence=0,
                    state='draft',
                    discount_money=order.solution_discount,
                ))

    def _apply_solution(self, order):
        """
            Builds sales order using solution as template.
            This can be called either during create or from wizard
        """

        quantities = dict([
            (ex.product.id, ex.times) for ex in order.solution.products_extra
        ])

        # Override order lines

        new_lines = self.env['sale.order.line']
        unit = self.env.ref('product.product_uom_categ_unit')

        delta_price = 0
        sequence = 0
        is_package = False

        if order.solution.default_code:
            is_package = True
            new_lines += new_lines.new(dict(
                order_id=order,
                #product_id #  No actual product. Will read solution code.
                name=order.solution.description or ' ',
                price_unit=order.solution.list_price,
                solution_part=0,
                product_uom_qty=1,
                product_uom=unit.id,
                sequence=sequence,
                state='draft',
                discount_money=0,
            ))

        for product in order.solution.products:

            sequence += 10
            qty = quantities.get(product.id, 1.0)

            new_lines += new_lines.new(dict(
                order_id=order,
                product_id=product,
                name=product.description_sale or ' ',
                product_uom_qty=qty,
                price_unit=not is_package and product.lst_price or 0,
                solution_part=is_package and 1 or 0,
                product_uom=product.uom_id,
                sequence=sequence,
                state='draft',
            ))

        for product in [
            item.product for item in order.solution.options_extra
            if item.selected_default
        ]:
            sequence += 10
            qty = quantities.get(product.id, 1.0)

            new_lines += new_lines.new(dict(
                order_id=order,
                product_id=product,
                name=product.description_sale or ' ',
                product_uom_qty=qty,
                price_unit=product.lst_price,
                solution_part=2,  # is_package and 2 or 0,
                product_uom=product.uom_id,
                sequence=sequence,
                state='draft',
            ))

        order.order_line = new_lines

    @api.onchange('solution')
    def onchange_solution(self):

        for order in self:
            self._apply_solution(order)

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
                line.solution_part != 1
                and line.price_unit and line.product_uom_qty
            ):
                line.discount_money = max(
                    0,
                    min(
                        line.discount_money,
                        line.product_uom_qty * line.price_unit))

                # line.discount = (
                #     100.0 * line.discount_money
                #     / line.product_uom_qty / line.price_unit
                # )
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

    @api.onchange('product_id')
    def _is_ad_line(self):
        for line in self:

            if not line.product_id or line.solution_part != 2:
                line.is_ad_line = False
                continue

            cat = line.product_id.categ_term

            line.is_ad_line = cat.id in [
                self.env.ref('xpr_product.advertising').id,
                self.env.ref('xpr_product.adwords').id
            ]

    @api.onchange('product_id')
    def _display_name(self):
        for line in self:

            if line.product_id:
                line.display_name = line.product_id.display_name
            elif line.solution_part == 0:
                line.display_name = line.order_id.solution.display_name
            else:
                line.display_name = ''

    @api.onchange('product_id')
    def _display_description(self):
        for line in self:

            if line.product_id:
                line.display_description = (line.product_id.description_sale or '').strip()
            else:
                line.display_description = (line.name or '').strip()

    # 0 Main/unpackaged (solution)
    # 1 mandatory composition of solution
    # 2 optional composition of solution

    solution_part = fields.Integer(default=0)

    display_name = fields.Char(string="Name", compute=_display_name)
    display_description = fields.Text(string="Description", compute=_display_description)

    discount_money = fields.Float(
        string='Discount ($)', digits=(6, 2), default=0)

    # Override required to redirect to new compute function.
    # Otherwise, function pointer still points to overriden version.
    price_subtotal = fields.Float(
        digits=(6, 2),
        string='Subtotal',
        digits_compute=dp.get_precision('Account'),
        compute=_amount_line)

    is_ad_line = fields.Boolean(string="Is Ad", readonly=True, compute=_is_ad_line)

    _defaults = {'name': ' '}


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
        ]) | set([
            item.product.id for item in self.solution.options_extra
            if item.sticky
        ])

        products_in_order = set()

        removed_lines = []

        sequence = 10
        for line in self.order.order_line:

            sequence = max(sequence, line.sequence)

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

            sequence += 10
            line.create(
                dict(
                    order_id=self.order.id,
                    product_id=product.id,
                    name=product.description_sale or ' ',
                    product_uom_qty=1.0,
                    solution_part=2,
                    sequence=sequence))

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


class SolutionCombiner(models.TransientModel):

    """
    Solution Combiner wizard.

    Loaded to build new solutions based on the combination of existing ones.
    """

    _name = 'xpr_solution_builder.solution_combiner'

    def _init_solution(self):

        context = self.env.context

        active_id = context.get('solution', context.get('active_id'))

        if not active_id:
            return None

        return self.env['xpr_solution_builder.solution'].browse(active_id)

    solution = fields.Many2one(
        'xpr_solution_builder.solution',
        string='Solution',
        required=True,
        default=_init_solution)

    combined_category = fields.Many2one(
        'product.category',
        string='Combined with Category',
        required=True)

    @api.one
    def combine_category(self):

        solutions = self.env['xpr_solution_builder.solution'].search([
            ('category', '=', self.combined_category.id),
            ('id', '!=', self.solution.id)
        ])

        for right_solution in solutions:
            combined = self.env['xpr_solution_builder.solution'].create(dict(
                name="{0}-{1}".format(
                    self.solution.name, right_solution.name),
                description="{0} {1}".format(
                    self.solution.description, right_solution.description),
                list_price=(
                    self.solution.list_price +
                    right_solution.list_price),
                default_code="{0}-{1}".format(
                    self.solution.default_code, right_solution.default_code),
            ))

            combined.products = (
                self.solution.products |
                right_solution.products
            )

            combined.products_extra = (
                self.solution.products_extra |
                right_solution.products_extra
            )

            combined.options = self.solution.options | right_solution.options
            combined.options_extra = (
                self.solution.options_extra |
                right_solution.options_extra
            )

            combined.category = self.solution.category
