# -*- coding: utf-8 -*-
from openerp import http

# class SolutionBuilder(http.Controller):
#     @http.route('/solution_builder/solution_builder/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/solution_builder/solution_builder/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('solution_builder.listing', {
#             'root': '/solution_builder/solution_builder',
#             'objects': http.request.env['solution_builder.solution_builder'].search([]),
#         })

#     @http.route('/solution_builder/solution_builder/objects/<model("solution_builder.solution_builder"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('solution_builder.object', {
#             'object': obj
#         })