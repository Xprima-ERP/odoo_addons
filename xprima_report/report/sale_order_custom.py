# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from sale.report import sale_order
from openerp.report import report_sxw
from netsvc import Service


class order(sale_order.order):
    def __init__(self, cr, uid, name, context):
        super(order, self).__init__(cr, uid, name, context=context)

# delete report
if 'report.sale.order' in Service._services.keys():
    del Service._services['report.sale.order']

report_sxw.report_sxw('report.sale.order',
                      'sale.order',
                      'addons/xprima_report/report/sale_order_xprima.rml',
                      parser=order,
                      header='external')

