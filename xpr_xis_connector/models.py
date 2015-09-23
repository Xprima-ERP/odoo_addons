# -*- encoding: utf-8 -*-
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

import logging
import time
import json
import utils
import xis_request
from openerp import models, fields, api
from openerp.tools.translate import _
from sets import Set

_logger = logging.getLogger(__name__)


class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    region = fields.One2many(
        'xpr_xis_connector.dealer.region',
        'category',
        string='Region Info'
    )

    certification = fields.One2many(
        'xpr_xis_connector.dealer.certification',
        'category',
        string='Certification Info'
    )


class DealerCategoryMixin():
    _inherits = {
        'res.partner.category': 'category'
    }

    def _get_name(self):
        for dealer_cat in self:
            dealer_cat.name = dealer_cat.category.name

    def create(self, cr, uid, vals, context=None):
        status = super(PartnerCategory, self).create(
            cr, uid, vals, context=context)

        req = _PartnerCategoryRequest(self, cr, uid, status, context=context)
        req.send_partner_category_xis()

        return status

    def write(self, cr, uid, ids, vals, context=None):
        status = super(PartnerCategory, self).write(
            cr, uid, ids, vals, context=context)

        if type(ids) is long or type(ids) is int:
            ids = [ids]

        for id_r in ids:
            req = _PartnerCategoryRequest(self, cr, uid, id_r, context=context)
            req.send_partner_category_xis()

        return status

    category = fields.Many2one(
        'res.partner.category',
        string="Category",
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(compute=_get_name)


class DealerRegion(models.Model, DealerCategoryMixin):

    """Extension of a category, that permits
    to describe region for a dealer"""

    _name = 'xpr_xis_connector.dealer.region'

    # Region code
    region_code = fields.Char('Region Code')


class DealerCertification(models.Model, DealerCategoryMixin):

    """Extension of a category, that permits
    to describe certifications for a dealer"""

    _name = 'xpr_xis_connector.dealer.certification'

    # Region code
    region_code = fields.Char('Region Code')


class Dealer(models.Model):

    _inherit = 'xpr_dealer.dealer'

    def _get_xis_makes(self):

        for dealer in self:
            makes = set(m.name for m in dealer.makes)
            #TODO: Check if order is important
            dealer.xis_makes = ','.join(makes)

        return {}

    def _get_area_code(self):

        for dealer in self:
            code = dealer.phone.replace('(', '').replace(')', '')
            code = code.replace('-', '').strip()

            if code[0] == '1':
                code[1:4]
            else:
                code[:3]

            if len(code.strip()) == 3:
                dealer.area_code = code
            else:
                dealer.area_code = ''

        return {}

    def _get_code(self):
        for dealer in self:
            dealer.xis_dc = dealer.code

    xis_makes = fields.Char(compute=_get_xis_makes)

    area_code = fields.Char(size=3, compute=_get_area_code)

    telephone_choice = fields.Selection(
        [
            ("phone", "Phone"),
            ("toll_free", "Toll Free"),
            ("call_tracking", "Evolio Call")
        ],
        "Phone Choice"
    )

    site_type = fields.Selection(
        [
            ("has_website_with_us", "Has Website With Us"),
            ("has_a_link_or_portals_to_their_site",
                "Has a link or portals to their site"),
            ("does_not_have_a_website", "Does not have a website")
        ],
        "Site Type"
    )

    # xis_dc redirects to 'code'
    xis_dc = fields.Char(compute=_get_code)

    owner = fields.Char(
        "Dealership Owner",
        size=45,
        help="This field is there for the synchronization to XIS")

    owneremail = fields.Char(
        "Dealership Owner Email",
        size=240,
        help="This field is there for the synchronization to XIS")

    user10 = fields.Char("User10", size=10)
    user12 = fields.Char("User12", size=12)
    user12e = fields.Char("User12e", size=12)
    user40 = fields.Char("User40", size=40)
    user40e = fields.Char("User40e", size=40)
    user80 = fields.Char("User80", size=80)

    market = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_market_rel',
        string="Market",
    )

    region = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_region_rel',
        string="Region",
    )

    portalmask = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_portal_rel',
        string="Used Cars On")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_ref(self):
        for order in self:
            order.xis_quote_id = order.client_order_ref

    xis_quote_id = fields.Integer(string='XIS quote id', compute=_get_ref)

    def __init__(self, pool, cr):
        super(SaleOrder, self).__init__(pool, cr)

    def create(self, cr, uid, vals, context=None):
        xis_val = {}
        status = super(SaleOrder, self).create(cr, uid, vals, context=context)

        qt_xisid = None
        so_req = SaleOrderRequest(self, cr, uid, status, context=context)
        data = so_req.get_xis_field(so_req)
        if data:
            xis_status, qt_xisid = so_req.send_quote_xis(data)

        # write to database
        if qt_xisid is not None:
            xis_val["xis_quote_id"] = qt_xisid
            super(SaleOrder, self).write(
                cr, uid, status, xis_val, context=context)

        return status

    def write(self, cr, uid, ids, vals, context=None):
        status = super(SaleOrder, self).write(
            cr, uid, ids, vals, context=context)

        for r_id in ids:
            is_new = False
            xis_val = {}
            qt_xisid = self.browse(cr, uid, r_id, context=context).xis_quote_id
            if not qt_xisid:
                # ok, create a new one
                qt_xisid = None
                is_new = True
            so_req = SaleOrderRequest(
                self, cr, uid,
                r_id,
                context=context,
                xis_id=qt_xisid)

            data = so_req.get_xis_field(so_req, is_update=True)
            if data:
                xis_status, qt_xisid = so_req.send_quote_xis(data)
                # write to database the xisid
                if is_new and qt_xisid is not None:
                    xis_val["xis_quote_id"] = qt_xisid
                    super(SaleOrder, self).write(
                        cr, uid, r_id, xis_val, context=context)

        return status

    # def onchange_partner_id(self, cr, uid, ids, part, context=None):
    #     result = super(sale_order, self).onchange_partner_id(cr,
    #                                                          uid,
    #                                                          ids,
    #                                                          part,
    #                                                          context)
    #     empty_pricelist = {'pricelist_id': False}
    #     result.get('value', {}).update(empty_pricelist)
    #     return result


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


class Partner(models.Model):

    _inherit = "res.partner"

    def create(self, cr, uid, vals, context=None):
        status = super(Partner, self).create(
            cr, uid, vals, context=context)

        if self.browse(cr, uid, status, context=context).customer:
            req = _PartnerRequest(self, cr, uid, status, context=context)
            req.send_partner_xis()

            dct_cat_vals = vals.get("category_id")
            if dct_cat_vals:
                lst_new_cat = [cat[2] for cat in dct_cat_vals][0]
                req = _PartnerCategoryRelRequest(self, cr, uid, status,
                                                 context=context,
                                                 add_id=lst_new_cat)
                req.send_partner_category_xis()

        return status

    def write(self, cr, uid, ids, vals, context=None):
        # Only the manager of the modifier can change the user_id of this
        # partner
        if 'user_id' in vals:
            authorized_modifiers_groups = ['Helpdesk / Agent',
                                           'Administration / Settings',
                                           'Sales / Manager',
                                           'Contact Creation', ]
            users_obj = self.pool.get('res.users')
            writer_user = users_obj.browse(cr, uid, uid)
            user_groups = [group.full_name for group in writer_user.groups_id]
            is_authorized = False
            for group in authorized_modifiers_groups:
                if group in user_groups:
                    if group == u'Sales / Manager':
                        # Need to be the manager of the user_id
                        # or the coach.
                        hr_emp_obj = self.pool.get('hr.employee')
                        partner = self.browse(cr, uid, ids[0])
                        s_args = [('user_id', '=', partner.user_id.id)]
                        try:
                            user_id_hr = hr_emp_obj.search(cr,
                                                           uid,
                                                           s_args,
                                                           context=context)[0]
                        except IndexError:
                            continue
                        user_hr = hr_emp_obj.browse(cr,
                                                    uid,
                                                    user_id_hr,
                                                    context)
                        manager_hr = user_hr.parent_id
                        coach_hr = user_hr.coach_id
                        if manager_hr:
                            if uid == manager_hr.user_id.id:
                                is_authorized = True
                                break
                        if coach_hr:
                            if uid == coach_hr.user_id.id:
                                is_authorized = True
                                break
                        if partner.user_id:
                            if uid == partner.user_id.id:
                                is_authorized = True
                                break
                    else:
                        is_authorized = True
                        break
            if not is_authorized:
                del vals['user_id']

        dct_cat_vals = vals.get("category_id")
        if dct_cat_vals:
            lst_new_cat = [cat[2] for cat in dct_cat_vals]
            lst_rec = self.browse(cr, uid, ids, context=context)
            lst_old_cat = [[cat.id for cat in rec.category_id] for rec in
                           lst_rec]

        status = super(Partner, self).write(
            cr, uid, ids, vals, context=context)

        if type(ids) is long or type(ids) is int:
            ids = [ids]

        i = 0
        for id_r in ids:
            if self.browse(cr, uid, id_r, context=context).customer:
                req = _PartnerRequest(self, cr, uid, id_r, context=context)
                req.send_partner_xis()
                if dct_cat_vals:
                    # add rel to dealer_group
                    new_cat = lst_new_cat[i]
                    old_cat = lst_old_cat[i]
                    # diff dealergroup
                    rem_cat = [x for x in old_cat if x not in set(new_cat)]
                    add_cat = [x for x in new_cat if x not in set(old_cat)]
                    req = _PartnerCategoryRelRequest(self, cr, uid, id_r,
                                                     context=context,
                                                     add_id=add_cat,
                                                     rem_id=rem_cat)
                    req.send_partner_category_xis()

            i += 1

        return status


class _PartnerRequest():

    """
    This private class merge model and vals and give method to request info.
    """

    def __init__(self, parent, cr, uid, r_id, context=None):
        self.xis_request = xis_request.XisRequest(_logger, cr, uid, parent)
        self.model_xis = "TTRDealerUpdater"
        # Dev
        self.url = "https://xis.xprima.com/ws/erp/dealers_sf.spy"
        # Live
        self.url = "https://xis-lb/ws/erp/dealers_sf.spy"

        utils.set_xis_fqdn(self, parent, cr, uid, context)

        # model
        self.partner = parent.browse(cr, uid, r_id, context=context)
        # Build dealerarea (province_code + area_code [+region_code])
        dealerarea = ''
        # The dealerarea for '905CADA','AUTO123MERC','CCAMA','PERSONALLA',
        # 'PERSONALMA','PERSONALNWT','PERSONALSA','PERSONALYU','514AVANTIPLUS'
        # don't follow the rule, and have to be hardcoded so as not to break
        # anything in XIS/TTR
        dealerarea_region_code = None
        if self.partner.xis_dc == '905CADA':
            dealerarea = '905'
        elif self.partner.xis_dc == 'AUTO123MERC':
            dealerarea = '514'
        elif self.partner.xis_dc == 'CCAMA':
            dealerarea = 'CCAMA'
        elif self.partner.xis_dc == 'PERSONALLA':
            dealerarea = 'LA'
        elif self.partner.xis_dc == 'PERSONALMA':
            dealerarea = 'MA'
        elif self.partner.xis_dc == 'PERSONALNWT':
            dealerarea = 'NWT'
        elif self.partner.xis_dc == 'PERSONALSA':
            dealerarea = 'SA'
        elif self.partner.xis_dc == 'PERSONALYU':
            dealerarea = 'YU'
        elif self.partner.xis_dc == '514AVANTIPLUS':
            dealerarea = '514'
        else:
            _state = self.partner.state_id
            if _state and self.partner.area_code:
                dealerarea_state = parent.pool.get('res.country.state')
                if _state:
                    dealerarea_state_code = dealerarea_state.browse(
                        cr, uid, _state.id, context=context).code
                dealerarea_area_code = self.partner.area_code
                dealerarea_region_code = False
                if self.partner.region:
                    obj_region = parent.pool.get('partner_region')
                    region_id = obj_region.search(
                        cr, uid, [('name', '=', self.partner.region)])[0]
                    try:
                        dealerarea_region_code = obj_region.browse(
                            cr, uid, region_id, context=context).code
                    except Exception:
                        pass
                try:
                    if dealerarea_region_code:
                        dealerarea = "%s%s%s" % (
                            dealerarea_state_code,
                            dealerarea_area_code,
                            dealerarea_region_code
                        )
                    else:
                        dealerarea = "%s%s" % (
                            dealerarea_state_code,
                            dealerarea_area_code,
                        )
                except Exception:
                    dealerarea = 'null'
        self.dealerarea = dealerarea
        # Build membertype
        # membertype are translated, the XIS api wants the englis terms.
        obj_partner_business_type = parent.pool.get('partner_business_type')
        pbt_ids = [type.id for type in self.partner.membertype]
        # Set the language to english so we dont get the translated terms for
        # the partner business types.
        if context:
            context.update({'lang': 'en_US'})
        else:
            context = {'lang': 'en_US'}
        result = obj_partner_business_type.read(cr,
                                                uid,
                                                pbt_ids,
                                                fields=['name'],
                                                context=context)
        membertype = [type.get('name') for type in result]
        self.str_membertype = ';'.join(membertype)
        # Build site type since it's translated and xis only accepts english.
        if self.partner.site_type_id.id:
            obj_site_type = parent.pool.get('partner_site_type')
            self.site_type = obj_site_type.read(cr,
                                                uid,
                                                self.partner.site_type_id.id,
                                                fields=['name'],
                                                context=context).get('name')
        else:
            self.site_type = 'null'

    def send_partner_xis(self):
        data = self._get_xis_field()
        if not data:
            return None
        xis_status = None
        status, response = self.xis_request.send_request(self.model_xis,
                                                         self.url,
                                                         data)
        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                xis_status = dct_response.get("status")

        return xis_status

    @staticmethod
    def get_last_modif_date():
        return time.strftime("%Y/%m/%d %H:%M:%S")

    def _get_xis_field(self):
        # validate data
        p = self.partner
        _pux = p.user_id.xis_user_external_id
        if not p.xis_dc or not _pux or not p.is_company:
            return None
        state = p.state_id and p.state_id.name or None
        if not state or state == "Quebec":
            state = "Québec"
        if state == "Newfoundland and Labrador":
            state = "Newfoundland"
        # Build customermask data.
        customermasks = []
        for cm in p.customermask_ids:
            customermasks.append(cm.name)
        s_customermasks = ';'.join(customermasks)
        # Build portalmask
        portalmask = [mask.name for mask in p.portalmask]
        str_portalmask = ';'.join(portalmask)
        # Build quoteflag
        if p.quoteflag:
            quoteflag = 'true'
        else:
            quoteflag = 'false'
        # Build ttr
        if p.ttr_access:
            ttr_access = 'true'
        else:
            ttr_access = 'false'
        # Build isdealer
        if p.is_dealer:
            isdealer = 'true'
        else:
            isdealer = 'false'
        # Build ismember
        if p.is_member:
            ismember = 'true'
        else:
            ismember = 'false'
        if p.market:
            market = p.market.lower()
        else:
            market = 'null'
        dealers = {
            'address': p.street or 'null',
            'buyit': 'false',
            'callsource_tollfree': p.callsource_tollfree or 'null',
            'city': p.city or 'null',
            'corpcontracts': p.pin or 'null',
            'corpname': p.corpname or 'null',
            'country': p.country and p.country.name or 'null',
            'customermask': s_customermasks or 'null',
            'dayspastdue': p.dayspastdue or 'null',
            'dealerarea': self.dealerarea or 'null',
            'dealercode': p.xis_dc.strip() or 'null',
            'dealeremail': 'null',  # must go from xis to OE.
            'dealername': p.name.strip() or 'null',
            'dealerurle': p.website or 'null',
            'dealerurlf': p.website_french or 'null',
            'dpd_override': '%s 00:00:00' % (p.dpd_override,) or 'null',
            'fax': p.fax or 'null',
            # '45.548255',
            'geolat': p.geolat or 'null',
            'geolon': p.geolon or 'null',
            #'isdealer': isdealer, # Deprecated
            #'ismember': ismember, # Deprecated

            # force to take 'en' of 'en_US'
            'language': p.lang and p.lang[:2] or 'null',
            'lastmoddate': self.get_last_modif_date(),
            'makes': p.xis_makes or 'null',
            'market': market or 'null',
            'membertype': self.str_membertype or 'null',
            'newemail': 'null',  # This field must go from xis to OE.
            'owner': p.owner or 'null',
            'owneremail': p.owneremail or 'null',

            'phone': p.phone or 'null',
            'phone2': p.mobile or 'null',
            'portalmask': str_portalmask or 'null',
            'postalcode': self.partner.zip or 'null',
            'province': state,
            'quoteflag': quoteflag,
            'responsible': p.responsible or 'null',
            'salesguy': p.user_id.xis_user_external_id or 'null',
            'sitetype': self.site_type or 'null',
            'tollfree': p.tollfree or 'null',
            'ttr': ttr_access,

            'usedemail': 'null',
            'user10': p.user10 or 'null',
            'user12': p.user12 or 'null',
            'user12e': p.user12e or 'null',
            'user40': p.user40 or 'null',
            'user40e': p.user40e or 'null',
            'user80': p.user80 or 'null',
        }

        data = {
            "dealers": [dealers],
            "honeypot_cedric": 'Metallica Rules',  # security key
        }
        return data


class _PartnerCategoryRequest():

    """
    This private class merge model and vals and give method to request info.
    """

    def __init__(self, parent, cr, uid, r_id, context=None):
        self.xis_request = xis_request.XisRequest(_logger, cr, uid, parent)
        self.parent = parent
        self.model_xis = "XisDealerGroupDescUpdater"
        # Dev
        self.url = 'https://xis.xprima.com/ws/erp/dealer_groups_sf.spy'
        # Live
        self.url = 'https://xis-lb/ws/erp/dealer_groups_sf.spy'

        # pool
        translate = parent.pool.get('ir.translation')
        lst_translate = translate.search(cr, uid, [
            ('name', '=', 'res.partner.category,description'),
            ('res_id', '=', r_id)], context=context)
        self.lst_desc = translate.browse(cr, uid, lst_translate)

        # model
        self.partner_category = parent.browse(cr, uid, r_id, context=context)

    def send_partner_category_xis(self):
        data = self._get_xis_field()
        if not data:
            return None
        xis_status = None
        status, response = self.xis_request.send_request(self.model_xis,
                                                         self.url,
                                                         data)
        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                xis_status = dct_response.get("status")

        return xis_status

    def _get_xis_field(self):
        # validate data
        p = self.parent.xis_info and self.parent.xis_info[0] or None

        # need a grouptype and id > 0
        if not p or not p.id or not p.parent_id or not p.name:
            return None
        # get description
        lst_desc_fr = [desc.value for desc in self.lst_desc if
                       "fr" in desc.lang]
        if lst_desc_fr:
            desc_fr = lst_desc_fr[0]
        else:
            desc_fr = p.description
        lst_desc_en = [desc.value for desc in self.lst_desc if
                       "en" in desc.lang]
        if lst_desc_en:
            desc_en = lst_desc_en[0]
        else:
            desc_en = p.description
        # cert_id = 0 if not p.certification else p.certification[
        #    0].xis_certification_id
        cert_id = p.xis_certification_id
        group = {
            'name': p.name,
            'certification_id': cert_id,
            'desc_en': desc_en,
            'desc_fr': desc_fr,
            'grouptype': p.parent_id.name,
        }
        data = {
            "dealergroup_desc": [group],
            "honeypot_roger": '1',  # security key
        }
        return data


class _PartnerCategoryRelRequest():

    """
    This private class merge model and vals and give method to request info.
    """

    def __init__(self, parent, cr, uid, r_id, context=None, add_id=[],
                 rem_id=[]):
        self.xis_request = xis_request.XisRequest(_logger, cr, uid,
                                                  parent)
        self.parent = parent
        self.model_xis = "XisDealerGroupDescUpdater"
        # Dev
        self.url = 'https://xis.xprima.com/ws/erp/dealer_groups_sf.spy'
        # Live
        self.url = 'https://xis-lb/ws/erp/dealer_groups_sf.spy'

        self.add_id = add_id
        self.rem_id = rem_id
        self.cr = cr
        self.uid = uid
        self.context = context

        # pool
        self.partner_cat_pool = parent.pool.get("res.partner.category")

        # model
        self.partner = parent.browse(cr, uid, r_id, context=context)

    def send_partner_category_xis(self):
        data = self._get_xis_field()
        if not data:
            return None
        xis_status = None
        status, response = self.xis_request.send_request(self.model_xis,
                                                         self.url,
                                                         data)
        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                xis_status = dct_response.get("status")

        return xis_status

    def _get_xis_field(self):
        # validate data
        p = self.partner
        pcp = self.partner_cat_pool
        if not p.is_company or not p.xis_dc:
            return None

        lst_group_add = []
        lst_group_rem = []
        for r_id in self.add_id:
            rec = pcp.browse(self.cr, self.uid, r_id, context=self.context)
            group = {
                'dealercode': p.xis_dc,
                'name': rec.name,
                'grouptype': rec.parent_id.name,
            }
            lst_group_add.append(group)

        for r_id in self.rem_id:
            rec = pcp.browse(self.cr, self.uid, r_id, context=self.context)
            group = {
                'dealercode': p.xis_dc,
                'name': rec.name,
                'grouptype': rec.parent_id.name,
            }
            lst_group_rem.append(group)

        data = {
            "to_add": lst_group_add,
            "to_remove": lst_group_rem,
            "honeypot_roger": '1',  # security key
        }
        return data


class Product(models.Model):
    _inherit = "product.template"

    def _get_code(self):
        for p in self:
            p.xis_product_code = p.default_code

    xis_product_code = fields.Char(
        'XIS product code', size=30, compute=_get_code)
