#!/usr/bin/env python2
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
import urllib
import urllib2
import logging
import time

_logger = logging.getLogger(__name__)


class XisRequest():

    """
    Class to send request to XIS software. Using POST http request.
    """

    def __init__(self, parent):
        self.parent = parent
        self.param_pool = parent.env['ir.config_parameter']

    def _get_url(self, page_name):
        # check configuration to active XIS connector
        is_enable = False

        lst_param = self.param_pool.search([
            ('key', '=', 'xis.enable.connector')])

        if lst_param:
            param = lst_param[0].value

            is_enable = param and (param == "1" or param.lower() == "true")

        if not is_enable:
            _logger.debug("xis.domain.connector is not set.")
            return None

        domain = None

        lst_param = self.param_pool.search(
            [('key', '=', 'xis.domain.connector')])

        if lst_param:
            domain = lst_param[0].value

        if not domain:
            _logger.debug("xis.domain.connector is not set.")
            return None

        # Live: xis.xprima.com
        # Dev: xis-lb

        return "https://{0}/ws/erp/{1}".format(domain, page_name)

    def send_request(self, model, page_name, values):
        """
        Send POST request to giving url (if not contain GET request).
        Send an email if request contain error.
        Return (status, output)
        """
        status = False
        result = None
        response = None
        _logger.debug(values)
        code = 0
        data = ""

        for key, value in values.items():
            if type(value) is dict:
                self.transfort_utf8_to_ascii_dict(value)

            if type(value) is list or type(value) is tuple:
                for item_value in value:
                    if type(item_value) is dict:
                        self.transfort_utf8_to_ascii_dict(item_value)

                    encode = urllib.urlencode(item_value)
                    encode = encode.replace("=", "%3D").replace("&", "%2C")
                    data += key + "=%5B%7B" + encode + "%7D%5D&"
                if not value:
                    data += key + "=%5B%5D&"
            else:
                non_encoded_keys = [
                    'qli_Description',
                    'qli_Name',
                    'qt_Comments',
                    'qt_IComments'
                ]
                re_encode = False
                for non_encoded_key in non_encoded_keys:
                    if non_encoded_key in key:
                        re_encode = True
                if re_encode and value:
                    try:
                        value.decode('utf-8')
                    except UnicodeEncodeError:
                        value = value.encode('utf-8')
                try:
                    data += urllib.urlencode(((key, value),)) + "&"
                except UnicodeEncodeError:
                    raise
        if data and data[-1:] == "&":
            # remove last '&'
            data = data[:-1]
        _logger.debug(data)

        url = self._get_url(page_name)

        if not url:
            # Not configured
            return True, None

        # send request
        req = urllib2.Request(url, data)
        error = None
        try:
            response = urllib2.urlopen(req)
            code = response.getcode()
            result = response.read()
        except urllib2.URLError as e:
            error = e
            code = e.code
            if hasattr(e, 'reason'):
                _logger.error(
                    'We failed to reach a server. Reason: %s' % e.reason)
            elif hasattr(e, 'code'):
                msg = 'The server couldn\'t fulfill the request. ' \
                      'Error code: %s' % code
                _logger.error(msg)
        finally:
            if not result:
                contains_error = True
            elif not error:
                contains_error = "errors" in result
            else:
                contains_error = False
            status = not (error or contains_error)
            if not status:
                self.send_email(model, data, result, code, error=error,
                                internal_error=contains_error)
        _logger.debug(result)
        return status, result

    @staticmethod
    def transfort_utf8_to_ascii_dict(dct):
        # remove utf8
        for key, item in dct.items():
            if type(item) is unicode:
                dct[key] = item.encode('utf8')

    def send_email(self, model, data, body, code, error=None,
                   internal_error=False):
        lst_email = []
        mail_pool = self.parent.pool.get('mail.mail')

        lst_param = self.param_pool.search(self.cr, self.uid,
                                           [('key', '=', 'xis.emails')])
        if lst_param:
            emails = self.param_pool.browse(self.cr, self.uid,
                                            lst_param[0]).value
            lst_email = emails.split(";")
            if lst_email:
                f_email = ','.join(lst_email)
        if not lst_email:
            return

        if error:
            str_ok = "NOT OK"
        else:
            str_ok = "OK"

        email_subject = 'OpenERP - %s Error' % model
        email_msg = 'HTTP RESPONSE STATUS CODE %s, value = %s' % (str_ok, code)
        if body and not internal_error:
            email_msg += '\nThe querystring to send was: \n' + data

            txt_body = '\t' + "\n\t".join(body.split("\n"))
            email_msg += '\nreturn:\n' + txt_body

        m_id = mail_pool.create(self.cr, self.uid, {
            'email_to': f_email,
            'subject': email_subject,
            'body_html': email_msg,
            'type': 'email'
        }, context=None)
        mail_pool.send(self.cr, self.uid, [m_id], context=None)


class XISRequestWrapper(object):

    model_xis = "NoModel"  # Subclasses must override this field

    def __init__(self, parent):
        self.xis_request = XisRequest(parent)
        self.order = parent

    def execute(self):
        raise Exception("Not implemented")


class SaleOrderRequest(XISRequestWrapper):

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

    model_xis = "XisDealerGroupDescUpdater"
    page_name = "proposal_sf.spy"

    def __init__(self, parent, is_update=False):

        super(SaleOrderRequest, self).__init__(parent)

        self.is_update = is_update

        # create pool
        self.config = parent.env['ir.config_parameter']
        self.order = parent

    def execute(self):

        qt_xisid = None
        xis_status = None

        data = self.get_xis_field()

        if not data:
            return xis_status

        status, response = self.xis_request.send_request(
            self.model_xis,
            self.page_name,
            data)

        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                qt_xisid = dct_response.get("qt_xisid")
                xis_status = dct_response.get("status")

            if qt_xisid is not None:
                self.order.client_order_ref = qt_xisid

        return xis_status

    def get_xis_field(self):
        ext_id = self.get_partner_ext_id()
        # cannot do a transaction without ext id
        # if not ext_id or not self.get_dealer_code():
        #     return

        nb_item = len(self.order.order_line)
        data = {
            # "123" sample base dealercode
            "qt_dc": self.get_dealer_code().strip(),

            # example of opportunity
            "qt_Opportunityid": 'null',
            "qt_CreatedDate": self.get_last_modif_date(),
            "qt_Comments": self.order.note,
            "qt_IComments": self.order.note,

            # Marc Cassuto  Sales Rep 736
            "qt_user_external_id__c": ext_id,
            "qt_StageName": self.get_state(),
            "qt_Language": self.get_language(),
            "qt_LastModifiedDate": self.get_last_modif_date(),

            # nb loop
            "num_line_item": nb_item,
            # security key
            "honeypot_cedric": 'Metallica Rules',
        }

        i = 0
        for line in self.order.order_line:
            data.update({
                "qli_ProductCode_%s" % i:
                line.product_id.default_code or "",

                "qli_ListPrice_%s" % i:
                int(line.product_uom_qty) * line.price_unit,

                "qli_Quantity_%s" % i: line.product_uom_qty,
                "qli_UnitPrice_%s" % i: line.price_unit,
                "qli_Name_%s" % i: line.name,
                "qli_Family_%s" % i: 'null',
                "qli_Description_%s" % i: line.name,
            })

            i += 1

        xis_id = self.get_xis_id()
        # check for debug xis_id

        # lst_param = self.config.search([
        #     ('key', '=', 'xis.debug.sale')])

        # if lst_param:
        #     param = lst_param[0]

        #     if param and (param == "1" or param.lower() == "true"):
        #         xis_id = "48305"

        if xis_id:
            data["qt_xisid"] = xis_id

        return data

    def get_xis_id(self):
        return self.order.client_order_ref

    def get_language(self):
        return self.order.env.context.get('lang', 'en')[:2]

    def get_dealer_code(self):
        # get partner info
        return self.order.partner_id and self.order.partner_id.code or ''

    def get_state(self):
        if self.is_update:
            return "NoChange"
        else:
            return self.dct_stage_asso.get(self.order.state)

    @staticmethod
    def get_last_modif_date():
        return time.strftime("%Y/%m/%d")

    def get_partner_ext_id(self):
        return self.order.user_id.xis_user_external_id


class PartnerRequest(XISRequestWrapper):

    """
    This private class merge model and vals and give method to request info.
    """

    model_xis = "TTRDealerUpdater"
    page_name = "dealers_sf.spy"

    def __init__(self, parent, old_categories):
        super(PartnerRequest, self).__init__(parent)

        self.old_categories = old_categories

        # This is already supported in superclass
        # utils.set_xis_fqdn(self, parent, cr, uid, context)

        # model
        self.partner = parent

        # Build dealerarea (province_code + area_code [+region_code])
        dealerarea = ''
        # The dealerarea for '905CADA','AUTO123MERC','CCAMA','PERSONALLA',
        # 'PERSONALMA','PERSONALNWT','PERSONALSA','PERSONALYU','514AVANTIPLUS'
        # don't follow the rule, and have to be hardcoded so as not to break
        # anything in XIS/TTR
        dealerarea_region_code = None
        if self.partner.code == '905CADA':
            dealerarea = '905'
        elif self.partner.code == 'AUTO123MERC':
            dealerarea = '514'
        elif self.partner.code == 'CCAMA':
            dealerarea = 'CCAMA'
        elif self.partner.code == 'PERSONALLA':
            dealerarea = 'LA'
        elif self.partner.code == 'PERSONALMA':
            dealerarea = 'MA'
        elif self.partner.code == 'PERSONALNWT':
            dealerarea = 'NWT'
        elif self.partner.code == 'PERSONALSA':
            dealerarea = 'SA'
        elif self.partner.code == 'PERSONALYU':
            dealerarea = 'YU'
        elif self.partner.code == '514AVANTIPLUS':
            dealerarea = '514'
        else:
            _state = self.partner.state_id
            if _state and self.partner.area_code:
                dealerarea_state = parent.env['res.country.state']
                if _state:
                    dealerarea_state_code = _state.id.code

                dealerarea_area_code = self.partner.area_code
                dealerarea_region_code = False
                if self.partner.region:
                    obj_region = parent.env['partner_region']
                    region_id = obj_region.search(
                        [('name', '=', self.partner.region)])[0]
                    try:
                        dealerarea_region_code = region_id.code
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
        obj_partner_business_type = parent.env['partner_business_type']
        pbt_ids = [type.id for type in self.partner.membertype]
        # Set the language to english so we dont get the translated terms for
        # the partner business types.

        self.env.context.update({'lang': 'en_US'})

        result = obj_partner_business_type.read(
            pbt_ids,
            fields=['name'])

        membertype = [type.get('name') for type in result]
        self.str_membertype = ';'.join(membertype)
        # Build site type since it's translated and xis only accepts english.
        if self.partner.site_type_id.id:
            obj_site_type = parent.env['partner_site_type']
            self.site_type = obj_site_type.read(
                self.partner.site_type_id.id,
                fields=['name']
            ).get('name')
        else:
            self.site_type = 'null'

    def execute(self):
        data = self._get_xis_field()

        xis_status = None

        if not data:
            return xis_status

        status, response = self.xis_request.send_request(
            self.model_xis,
            self.page_name,
            data)

        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                xis_status = dct_response.get("status")

        if xis_status and (self.old_categories or self.partner.category_id):

            new_categories = set([cat.id for self.partner.category_id])

            if new_categories != self.old_categories:
                PartnerCategoryRelRequest(
                    self.partner,
                    add_id=new_categories - self.old_categories,
                    rem_id=self.old_categories - new_categories).execute()

        return xis_status

    @staticmethod
    def get_last_modif_date():
        return time.strftime("%Y/%m/%d %H:%M:%S")

    def _get_xis_field(self):
        # validate data
        p = self.partner
        _pux = p.user_id.xis_user_external_id
        if not p.code or not _pux or not p.is_company:
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
            'dealercode': p.code.strip() or 'null',
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


class PartnerCategoryRequest(XISRequestWrapper):

    """
    This private class merge model and vals and give method to request info.
    """

    model_xis = "XisDealerGroupDescUpdater"
    page_name = "dealer_groups_sf.spy"

    def __init__(self, parent):
        super(PartnerCategoryRequest, self).__init__(parent)

        # pool
        translate = parent.env['ir.translation']
        self.lst_desc = translate.search([
            ('name', '=',
                'xpr_xis_connector.dealer.certification,description'),
            ('res_id', '=', parent.id)])

        # model
        self.partner_category = parent.category

    def execute(self):
        data = self._get_xis_field()
        if not data:
            return None

        xis_status = None
        status, response = self.xis_request.send_request(
            self.model_xis,
            self.page_name,
            data)

        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                xis_status = dct_response.get("status")

        return xis_status

    def _get_xis_field(self):
        # raise Exception("not implemeted")
        return {}


class PartnerRegionRequest(PartnerCategoryRequest):
    # Surprisingly, there is no XIS support for regions yet.
    pass


class PartnerCertificationRequest(PartnerCategoryRequest):

    def _get_xis_field(self):
        # validate data

        p = self.parent

        # need a grouptype and id > 0
        if not p.category or not p.category.parent_id or not p.name:
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

        group = {
            'name': p.name,
            'certification_id': p.xis_certification_id,
            'desc_en': desc_en,
            'desc_fr': desc_fr,
            'grouptype': "{certification} {certification_root}".format(
                certification=p.parent_id.name,
                certification_root=p.parent_id.parent_id.name),
        }
        data = {
            "dealergroup_desc": [group],
            "honeypot_roger": '1',  # security key
        }

        return data


class PartnerCategoryRelRequest(XISRequestWrapper):

    """
    This private class merges model and vals and give method to request info.
    """

    model_xis = "XisDealerGroupDescUpdater"
    page_name = "dealer_groups_sf.spy"

    def __init__(
        self, parent, add_id=set(), rem_id=set()
    ):
        super(PartnerCategoryRelRequest, self).__init__(parent)

        self.add_id = add_id
        self.rem_id = rem_id

        # pool
        self.partner_cat_pool = parent.env["res.partner.category"]

        # model
        self.partner = parent

    def execute(self):
        data = self._get_xis_field()
        if not data:
            return None

        xis_status = None
        status, response = self.xis_request.send_request(
            self.model_xis,
            self.page_name,
            data)

        # validate response
        if response:
            dct_response = json.loads(response)
            if type(dct_response) is dict:
                xis_status = dct_response.get("status")

        return xis_status

    def _get_xis_field(self):
        # validate data

        pcp = self.partner_cat_pool

        if not self.partner.is_company or not self.partner.code:
            return None

        lst_group_add = [
            {
                'dealercode': self.partner.code,
                'name': rec.name,
                'grouptype': rec.parent_id.name,
            } for rec in pcp.browse(self.add_id)
        ]

        lst_group_rem = [
            {
                'dealercode': self.partner.code,
                'name': rec.name,
                'grouptype': rec.parent_id.name,
            } for rec in pcp.browse(self.rem_id)
        ]

        data = {
            "to_add": lst_group_add,
            "to_remove": lst_group_rem,
            "honeypot_roger": '1',  # security key
        }
        return data
