# -*- coding: utf-8 -*-
from openerp import http

# class XprPreQuoteCreationActions(http.Controller):
#     @http.route('/xpr_pre_quote_creation_actions/xpr_pre_quote_creation_actions/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/xpr_pre_quote_creation_actions/xpr_pre_quote_creation_actions/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('xpr_pre_quote_creation_actions.listing', {
#             'root': '/xpr_pre_quote_creation_actions/xpr_pre_quote_creation_actions',
#             'objects': http.request.env['xpr_pre_quote_creation_actions.xpr_pre_quote_creation_actions'].search([]),
#         })

#     @http.route('/xpr_pre_quote_creation_actions/xpr_pre_quote_creation_actions/objects/<model("xpr_pre_quote_creation_actions.xpr_pre_quote_creation_actions"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('xpr_pre_quote_creation_actions.object', {
#             'object': obj
#         })