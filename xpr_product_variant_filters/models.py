# -*- coding: utf-8 -*-

from openerp import models, fields


class Product(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    def create_variant_ids(self, cr, uid, ids, context=None):
        """
        Calls super().create_variant_ids and delete variants that are not
        included in the filters
        """

        result = super(Product, self).create_variant_ids(cr, uid, ids, context)

        if not result:
            return result

        templates = self.browse(cr, uid, ids, context=context)
        product_obj = self.pool.get("product.product")

        variants_to_remove = []

        for template in templates:
            # We don't want to delete the product associated to the template

            if template.product_variant_count <= 1:
                continue

            # Load accepted combinations for this product.template
            filter_obj = self.pool.get('pvf.filter')
            args = [('template_id', '=', template.id)]
            filter_ids = filter_obj.search(cr, uid, args)
            filters = filter_obj.browse(
                cr,
                uid,
                filter_ids,
                context=context
            )

            if not filters.exists():
                # No filters set. Use default behavior.
                continue

            # Filter out the non logical combinations
            for prod_variant in template.product_variant_ids:
                var_attribute_value = prod_variant.attribute_value_ids
                if var_attribute_value not in [
                    _filter.product_attribute_value_ids for _filter in
                    filters
                ]:
                    variants_to_remove.append(prod_variant.id)

            # Remove the non logical variants
            product_obj.unlink(cr, uid, variants_to_remove, context=context)

        return result

class Filter(models.Model):
    _name = 'pvf.filter'

    product_attribute_value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        string='Logical Combination',
        required=True
    )

    template_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        required=True
    )
