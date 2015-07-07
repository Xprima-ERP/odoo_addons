# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
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
import logging
import xis_request
import time
import json
from openerp.tools.translate import _

from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)


class sale_order(orm.Model):
    _inherit = "sale.order"

    def _get_family(self, cr, uid, context, name):
        family_obj = self.pool.get('attribute.option')
        one_time_family_id = family_obj.search(cr,
                                               uid,
                                               [('name',
                                                 '=',
                                                 name)],
                                               limit=1,
                                               context=context)[0]
        family = family_obj.browse(cr, uid, one_time_family_id, context)
        return family

    def _get_one_time_total(self, cr, uid, ids, field_name, arg, context):
        one_time_fam_name = 'One Time'
        ad_one_time_fam_name = 'Advertising - One time'
        pack_one_time_fam_name = 'Package option - One time'
        one_time_family = self._get_family(cr, uid, context, one_time_fam_name)
        ad_one_time_family = self._get_family(cr,
                                              uid,
                                              context,
                                              ad_one_time_fam_name)
        pack_one_time_family = self._get_family(cr,
                                                uid,
                                                context,
                                                pack_one_time_fam_name)
        one_time_families = [one_time_family,
                             ad_one_time_family,
                             pack_one_time_family]
        sale_orders = self.browse(cr, uid, ids, context)
        one_time_totals = {}
        one_time_total = 0.0
        for sale_order in sale_orders:
            for line in sale_order.order_line:
                is_one_time = False
                try:
                    is_one_time = line.product_id.x_family in one_time_families
                except AttributeError:
                    pass
                if is_one_time:
                    one_time_total += line.price_subtotal
            one_time_totals[sale_order.id] = one_time_total
            one_time_total = 0.0
        return one_time_totals


    def _get_monthly_total(self, cr, uid, ids, field_name, arg, context):
        monthly_fam_name = 'Monthly'
        package_fam_name = 'Package'
        advert_fam_name = 'Advertising'
        pack_option_fam_name = 'Package option'
        monthly_family = self._get_family(cr, uid, context, monthly_fam_name)
        package_family = self._get_family(cr, uid, context, package_fam_name)
        advert_family = self._get_family(cr, uid, context, advert_fam_name)
        p_option_family = self._get_family(cr,
                                           uid,
                                           context,
                                           pack_option_fam_name)
        monthly_families = [monthly_family,
                            package_family,
                            p_option_family,
                            advert_family]
        sale_orders = self.browse(cr, uid, ids, context)
        monthly_totals = {}
        monthly_total = 0.0
        for sale_order in sale_orders:
            for line in sale_order.order_line:
                is_monthly = False
                try:
                    is_monthly = line.product_id.x_family in monthly_families
                except AttributeError:
                    pass
                if is_monthly:
                    monthly_total += line.price_subtotal/line.product_uom_qty
            monthly_totals[sale_order.id] = monthly_total
            monthly_total = 0.0
        return monthly_totals

    _columns = {
        'xis_quote_id': fields.integer(string='XIS quote id'),
        'one_time_total': fields.function(_get_one_time_total,
                                          type='float',
                                          obj='sale.order',
                                          method=True,
                                          string='One Time Total'),
        'monthly_total': fields.function(_get_monthly_total,
                                         type='float',
                                         obj='sale.order',
                                         method=True,
                                         string='Monthly Total'),
        'starting_date': fields.date('Starting Date'),
    }

    def __init__(self, pool, cr):
        super(sale_order, self).__init__(pool, cr)

    def create(self, cr, uid, vals, context=None):
        xis_val = {}
        status = super(sale_order, self).create(cr, uid, vals, context=context)

        qt_xisid = None
        so_req = SaleOrderRequest(self, cr, uid, status, context=context)
        data = so_req.get_xis_field(so_req)
        if data:
            xis_status, qt_xisid = so_req.send_quote_xis(data)

        # write to database
        if qt_xisid is not None:
            xis_val["xis_quote_id"] = qt_xisid
            super(sale_order, self).write(cr, uid, status, xis_val,
                                          context=context)

        return status

    def write(self, cr, uid, ids, vals, context=None):
        status = super(sale_order, self).write(cr, uid, ids, vals,
                                               context=context)
        for r_id in ids:
            is_new = False
            xis_val = {}
            qt_xisid = self.browse(cr, uid, r_id, context=context).xis_quote_id
            if not qt_xisid:
                # ok, create a new one
                qt_xisid = None
                is_new = True
            so_req = SaleOrderRequest(self, cr, uid,
                                      r_id,
                                      context=context,
                                      xis_id=qt_xisid)
            data = so_req.get_xis_field(so_req, is_update=True)
            if data:
                xis_status, qt_xisid = so_req.send_quote_xis(data)
                # write to database the xisid
                if is_new and qt_xisid is not None:
                    xis_val["xis_quote_id"] = qt_xisid
                    super(sale_order, self).write(cr, uid, r_id, xis_val,
                                                  context=context)

        return status

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        result = super(sale_order, self).onchange_partner_id(cr,
                                                             uid,
                                                             ids,
                                                             part,
                                                             context)
        empty_pricelist = {'pricelist_id': False}
        result.get('value', {}).update(empty_pricelist)
        return result


class SaleOrderRequest():

    """
    This private class merge model and vals and give method to request info.
    """
    dct_stage_asso = {
        "draft": "Introduction",
        "discounted": "Qualification",
        "2nd_approval": "Qualification",
        "validated": "Presentation",
        "sent": "Presentation",
        "cancel": "Closed Lost",
        "waiting_date": "Presentation",
        "progress": "Closing",
        "manual": "Closing",
        "shipping_except": "Delivered",
        "invoice_except": "Presentation",
        "done": "Signed",
    }

    def __init__(self, parent_class, cr, uid, r_id, context=None,
                 xis_id=None):
        self.xis_request = xis_request.XisRequest(_logger, cr, uid,
                                                  parent_class)
        self.model_xis = "XisDealerGroupDescUpdater"
        # Dev
        self.url_xis = 'https://xis.xprima.com/ws/erp/proposal_sf.spy'
        # Live
        self.url_xis = 'https://xis-lb/ws/erp/proposal_sf.spy'

        self.parent_class = parent_class
        self.cr = cr
        self.uid = uid
        self.r_id = r_id
        self.context = context
        self.xis_id = xis_id

        # create pool
        self.pool_param = parent_class.pool.get('ir.config_parameter')
        self.pool_partner = parent_class.pool.get('res.partner')
        self.pool_product = parent_class.pool.get('product.product')
        self.pool_order_line = self.parent_class.pool.get('sale.order.line')

        # model
        self.order = self.parent_class.browse(self.cr, self.uid,
                                              self.r_id,
                                              context=self.context)
        self.partner_req = self.order.partner_id
        self.line_order = self.order.order_line

    def send_quote_xis(self, data):
        qt_xisid = None
        xis_status = None
        status, response = self.xis_request.send_request(self.model_xis,
                                                         self.url_xis,
                                                         data)
        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                qt_xisid = dct_response.get("qt_xisid")
                xis_status = dct_response.get("status")

        return xis_status, qt_xisid

    def get_xis_field(self, so_req, is_update=False):
        ext_id = so_req.get_partner_ext_id()
        # cannot do a transaction without ext id
        if not ext_id or not so_req.get_dealer_code():
            return
        nb_item = so_req.get_order_line_size()
        data = {
            # "123" sample base dealercode
            "qt_dc": so_req.get_dealer_code().strip(),

            # example of opportunity
            "qt_Opportunityid": 'null',
            "qt_CreatedDate": so_req.get_last_modif_date(),
            "qt_Comments": self.order.note,
            "qt_IComments": self.order.note,

            # Marc Cassuto  Sales Rep 736
            "qt_user_external_id__c": ext_id,
            "qt_StageName": so_req.get_state(is_update),
            "qt_Language": so_req.get_language(),
            "qt_LastModifiedDate": so_req.get_last_modif_date(),

            # nb loop
            "num_line_item": nb_item,
            # security key
            "honeypot_cedric": 'Metallica Rules',
        }

        i = 0
        for i in range(nb_item):
            data["qli_ProductCode_%s" % i] = so_req.get_product_code(i)
            data["qli_ListPrice_%s" % i] = so_req.get_list_price(i)
            data["qli_Quantity_%s" % i] = so_req.get_quantity(i)
            # data["qli_Subtotal_%s" % i] = so_req.get_sub_total(i)
            # data["qli_TotalPrice_%s" % i] = so_req.get_total_price(i)
            data["qli_UnitPrice_%s" % i] = so_req.get_unit_price(i)
            data["qli_Name_%s" % i] = so_req.get_product_name(i)
            data["qli_Family_%s" % i] = 'null'
            data["qli_Description_%s" % i] = so_req.get_description(i)

        xis_id = so_req.get_xis_id()
        # check for debug xis_id
        lst_param = self.pool_param.search(self.cr, self.uid,
                                           [('key', '=',
                                             'xis.debug.sale')])
        if lst_param:
            param = self.pool_param.browse(self.cr, self.uid,
                                           lst_param[0]).value
            if param and (param == "1" or param.lower() == "true"):
                xis_id = "48305"

        if xis_id:
            data["qt_xisid"] = xis_id
        return data

    def get_xis_id(self):
        return self.xis_id

    def get_language(self):
        if self.context:
            lan = self.context.get('lang', 'en')
            lan = lan[:2]
        else:
            lan = 'en'
        return lan

    def get_dealer_code(self):
        # get partner info
        return self.partner_req.xis_dc

    def get_state(self, is_update=False):
        if is_update:
            return "NoChange"
        else:
            return self.dct_stage_asso.get(self.order.state)

    @staticmethod
    def get_last_modif_date():
        return time.strftime("%Y/%m/%d")

    def get_partner_ext_id(self):
        return self.order.user_id.xis_user_external_id

    def get_order_line_size(self):
        return len(self.line_order)

    def get_product_code(self, index):
        # "123" for demo
        if index >= len(self.line_order):
            return ""
        value = self.line_order[index].product_id.xis_product_code
        if value is False:
            return ""
        return value

    def get_list_price(self, index):
        if index >= len(self.line_order):
            return ""
        return int(self.line_order[index].product_uom_qty) * self.line_order[
            index].price_unit

    def get_quantity(self, index):
        if index >= len(self.line_order):
            return ""
        return int(self.line_order[index].product_uom_qty)

    def get_sub_total(self, index):
        if index >= len(self.line_order):
            return ""
        return self.line_order[index].price_subtotal

    def get_total_price(self, index):
        if index >= len(self.line_order):
            return ""
        line = self.line_order[index]
        subtotal = self.line_order[index].price_subtotal
        lst_tax = [subtotal * tax.amount for tax in line.tax_id]
        total_price = sum(lst_tax) + subtotal
        return total_price

    def get_unit_price(self, index):
        if index >= len(self.line_order):
            return ""
        return self.line_order[index].price_unit

    def get_product_name(self, index):
        if index >= len(self.line_order):
            return ""
        return self.line_order[index].name

    def get_description(self, index):
        if index >= len(self.line_order):
            return ""
        return self.line_order[index].name

    @staticmethod
    def _get_field_from_dct(req, field, default=""):
        if req is not False:
            value = req.get(field, default)
            if value is False:
                value = default
        else:
            value = default
        return value
