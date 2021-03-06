# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2010 - 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api
from openerp.tools.translate import _


class Company(models.Model):
    _inherit = "res.company"

    # Overwriting parent fields to make them translatable
    rml_header = fields.Text(string="RML Header", required=True, translate=True)
    rml_footer = fields.Text(
        string="Report Footer",
        help="Footer text displayed at the bottom of all reports.",
        required=True,
        translate=True)

# class order(report_sxw.rml_parse):
#     def __init__(self, cr, uid, name, context=None):
#         # Enriches report render context
#         super(order, self).__init__(cr, uid, name, context=context)
#         self.localcontext.update({
#             'time': time,
#             #'show_discount': self._show_discount,
#         })


# report_sxw.report_sxw(
#     'report.sale.order',
#     'sale.order',
#     'addons/xpr_report/report/sale_order_xprima.rml',
#     parser=order,
#     header='external')
