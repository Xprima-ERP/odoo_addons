# -*- coding: utf-8 -*-

##############################################################################
#
#  Adapted from package_configurator 7.0, Savoire-Faire Linux  
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _

class solution_configurator(orm.TransientModel):

    """Solution Configurator wizard"""

    _name = 'xpr_solution_builder.solution_configurator'
    #_description = __doc__

    _columns = {
        'order_id' : fields.many2one('sales.order',string='Order', required=True),
    #    'solution_id' : fields.many2one('xpr_solution_builder.solution',string='Solution',required=True),
    #    'product_ids' : fields.many2many('product.product', 'xpr_solution_builder_solution_configurator_product_rel', string='Product'),
    }


    # def _filter_product_dropdown(self, active_sale_order):
    #     '''
    #     Returns a {} containing the domain of the dropdown.
    #     '''
    #     domain = {}
    #     pricelist = active_sale_order.pricelist_id
    #     # Get the list of objects in this pricelist.
    #     if not pricelist:
    #         return False
    #     pricelist_version = pricelist.version_id[0]
    #     domain_filters = []
    #     if len(pricelist_version.items_id) != 1:
    #         domain_filters.append('|')
    #     for i, item in enumerate(pricelist_version.items_id):
    #         _xpc = 'xis_product_code'
    #         domain_filters.append((_xpc, '=', '%s' % item.name))
    #         if not ((i + 2) >= len(pricelist_version.items_id)):
    #             domain_filters.append('|')
    #     domain_filters.append(('sale_ok', '=', True))
    #     domain_filters
    #     return domain_filters

    def fields_view_get(
        self,
        cr,
        uid,
        view_id=None,
        view_type='form',
        context=None,
        toolbar=False,
        submenu=False
    ):
        ret = {}

        # ret = super(solution_configurator, self).fields_view_get(
        #     cr,
        #     uid,
        #     view_id,
        #     view_type,
        #     context,
        #     toolbar,
        #     submenu)

        # if ret.get('fields', {}).get('current_product_id') and ret.get('arch'):
        #     active_sale_order_id = context.get('active_id')
        #     sale_order_obj = self.pool.get('sale.order')
        #     active_sale_order = sale_order_obj.browse(cr,
        #                                               uid,
        #                                               active_sale_order_id,
        #                                               context)
        #     domain = self._filter_product_dropdown(active_sale_order)
        #     ret.get('fields').get('current_product_id')['domain'] = domain
        #     ret['arch'] = ret.get('arch').replace('domain="[(\'name\', ' \
        #      '\'=\', \'to_be_replaced_in_fields_view_get\')]"', 'domain=' \
        #      '"%s"' % domain)
        return ret

    # def onchange_solution_id(
    #     self,
    #     cr,
    #     uid,
    #     ids,
    #     product_category_id,
    #     is_level2,
    #     context=None
    # ):
        
    #     ret = {}

    #     if self.solution_id:
    #         domain = self._filter_solution_dropdown()

    #         ret.setdefault('domain', {})['current_product_id'] = domain
    #     return ret
