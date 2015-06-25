# -*- coding: utf-8 -*-
from openerp import http

# class ProductVariantsFilters(http.Controller):
#     @http.route('/product_variants_filters/product_variants_filters/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_variants_filters/product_variants_filters/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_variants_filters.listing', {
#             'root': '/product_variants_filters/product_variants_filters',
#             'objects': http.request.env['product_variants_filters.product_variants_filters'].search([]),
#         })

#     @http.route('/product_variants_filters/product_variants_filters/objects/<model("product_variants_filters.product_variants_filters"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_variants_filters.object', {
#             'object': obj
#         })