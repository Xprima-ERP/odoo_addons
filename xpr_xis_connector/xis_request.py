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
import json

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
            ('key', '=', 'xis.connector.enable')])

        if lst_param:
            param = lst_param[0].value

            is_enable = param and (param == "1" or param.lower() == "true")

        if not is_enable:
            _logger.info("xis.connector.enable is not set.")
            return None

        domain = None

        lst_param = self.param_pool.search(
            [('key', '=', 'xis.connector.domain')])

        if lst_param:
            domain = lst_param[0].value

        if not domain:
            _logger.info("xis.connector.domain is not set.")
            return None

        lst_param = self.param_pool.search(
            [('key', '=', 'xis.connector.protocol')])

        if lst_param:
            protocol = lst_param[0].value
        else:
            protocol = "http"

        return "{0}://{1}/ws/erp/{2}".format(protocol, domain, page_name)

    def send_request(self, model, page_name, values):
        """
        Send POST request to giving url (if not contain GET request).
        Send an email if request contain error.
        Return (status, output)
        """

        status = False
        result = None
        response = None
        code = 0

        url = self._get_url(page_name)

        if not url:
            # Not configured
            return True, None

        # send request
        print '----------------', values
        data = "&".join([
            "{0}={1}".format(
                key,
                urllib.quote_plus(json.dumps(value)))
            for key, value in values.items()
        ])

        req = urllib2.Request(url, data)

        error = None
        code = ''
        try:
            response = urllib2.urlopen(req, timeout=10)
            code = response.getcode()
            result = response.read()
        except urllib2.URLError as e:
            error = e
            if hasattr(e, 'reason'):
                _logger.error(
                    'We failed to reach a server. Reason: %s' % e.reason)
            elif hasattr(e, 'code'):
                msg = 'The server couldn\'t fulfill the request. ' \
                      'Error code: %s' % code
                code = e.code
                _logger.error(msg)
            raise
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

    def send_email(self, model, data, body, code, error=None,
                   internal_error=False):
        lst_email = []
        env = self.parent.env

        mail_pool = env['mail.mail']
        lst_param = self.param_pool.search([('key', '=', 'xis.emails')])

        if lst_param:
            emails = self.param_pool.browse(lst_param[0]).value
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

        m_id = mail_pool.create({
            'email_to': f_email,
            'subject': email_subject,
            'body_html': email_msg,
            'type': 'email'
        })

        mail_pool.send(self.cr, self.uid, [m_id], context=None)


class XISRequestWrapper(object):

    model_xis = "NoModel"  # Subclasses must override this field

    def __init__(self, parent):
        self.xis_request = XisRequest(parent)
        self.order = parent
        self.parent = parent

    def get_xis_data(self):
        """
        Override this to generate data to be sent to XIS
        """
        return {}

    def process_response(self, dct_response):
        """
        Extend this to process response dictionnary from XIS.
        Returns xis status by default
        """
        return dct_response.get("status")

    def execute(self):

        data = self.get_xis_data()

        if not data:
            return False

        status, response = self.xis_request.send_request(
            self.model_xis,
            self.page_name,
            data)

        # validate response
        if not response:
            # Default response to status update. Permits better dry runs.
            return self.process_response({'status': status})

        dct_response = json.loads(response)

        if type(dct_response) is not dict:
            return False

        return self.process_response(dct_response)


class SaleOrderRequest(XISRequestWrapper):

    """
    This private class merges model and vals and give method to request info.
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

        "need_manager_approval": "Presentation",
        "manager_approved": "Presentation",
        "manager_not_approved": "Presentation",
        "contract_not_presented": "Presentation",
        "contract_not_approved": "Presentation",
        "need_availability_check": "Presentation",
        "contract_approved": "Signed",
    }

    model_xis = "XisDealerGroupDescUpdater"
    page_name = "proposal_sf.spy"

    def __init__(self, parent):

        super(SaleOrderRequest, self).__init__(parent)
        self.order = parent

    def process_response(self, dct_response):
        """
        Inits order ref from XIS
        """
        qt_xisid = dct_response.get("qt_xisid")

        if qt_xisid is not None:
            self.order.client_order_ref = qt_xisid

        return super(SaleOrderRequest, self).process_response(dct_response)

    def get_xis_data(self):
        ext_id = self.get_partner_ext_id()
        # cannot do a transaction without ext id
        # if not ext_id or not self.get_dealer_code():
        #     return

        nb_item = len(self.order.order_line)
        data = {
            # "123" sample base dealercode
            "qt_dc": self.get_dealer_code().strip(),

            # example of opportunity
            "qt_Opportunityid": '',
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
        return self.dct_stage_asso.get(self.order.state)

    @staticmethod
    def get_last_modif_date():
        return time.strftime("%Y/%m/%d")

    def get_partner_ext_id(self):
        return self.order.user_id.xis_user_external_id


class DealerRequest(XISRequestWrapper):

    """
    This private class merge model and vals and give method to request info.
    """

    model_xis = "TTRDealerUpdater"
    page_name = "dealers_sf.spy"

    def __init__(self, dealer, old_categories=None):
        super(DealerRequest, self).__init__(dealer)

        self.partner = dealer.partner
        self.dealer = dealer
        self.old_categories = old_categories

    @staticmethod
    def get_last_modif_date():
        return time.strftime("%Y/%m/%d %H:%M:%S")

    def get_dealerarea(self):
        """
        Date field helper. Calculates area code.
        """

        # Build dealerarea (province_code + area_code [+region_code])

        # The dealerarea for '905CADA','AUTO123MERC','CCAMA','PERSONALLA',
        # 'PERSONALMA','PERSONALNWT','PERSONALSA','PERSONALYU','514AVANTIPLUS'
        # don't follow the rule, and have to be hardcoded so as not to break
        # anything in XIS/TTR

        if self.partner.code == '905CADA':
            return '905'
        if self.partner.code == 'AUTO123MERC':
            return '514'
        if self.partner.code == 'CCAMA':
            return 'CCAMA'
        if self.partner.code == 'PERSONALLA':
            return 'LA'
        if self.partner.code == 'PERSONALMA':
            return 'MA'
        if self.partner.code == 'PERSONALNWT':
            return 'NWT'
        if self.partner.code == 'PERSONALSA':
            return 'SA'
        if self.partner.code == 'PERSONALYU':
            return 'YU'
        if self.partner.code == '514AVANTIPLUS':
            return '514'

        _state = self.partner.state_id

        dealerarea_area_code = self.get_area_code()

        if not _state or not dealerarea_area_code:
            return ''

        dealerarea_state_code = _state.code

        if self.dealer.region:

            return "%s%s%s" % (
                dealerarea_state_code,
                dealerarea_area_code,
                self.dealer.region.region.region_code
            )

        return "%s%s" % (
            dealerarea_state_code,
            dealerarea_area_code,
        )

    def get_member_type(self):
        """
        Build member type string.
        """
        # Set the language to english so we dont get the translated terms for
        # the partner business types.

        dealer_en = self.dealer.with_context(lang='en_US')

        businesses = [
            b.name for b in dealer_en.business
        ]

        industries = set(m.parent_id.name for m in dealer_en.makes)

        return ";".join([
            "{0} {1}".format(b, i) for b in businesses for i in industries
        ])

    def get_site_type(self):

        # Build site type since it's translated and xis only accepts english.

        return {
            "has_website_with_us": "Has Website With Us",

            "has_a_link_or_portals_to_their_site":
            "Has a link or portals to their site",

            "does_not_have_a_website": "Does not have a website",
        }.get(self.dealer.site_type)

    def get_salesrep_ext_id(self):
        # Get current user XIS id
        return self.partner.env.user.xis_user_external_id

    def get_state(self):
        p = self.partner

        state = p.state_id and p.state_id.name or ''

        if not state or state == "Quebec":
            state = "Québec"
        if state == "Newfoundland and Labrador":
            state = "Newfoundland"

        return state

    def get_customermasks(self):
        return ';'.join(cm.name for cm in self.dealer.customer)

    def get_portalmask(self):
        return ';'.join(mask.name for mask in self.dealer.portalmask)

    def get_xis_makes(self):

        makes = set(m.name for m in self.dealer.makes)
        return ','.join(makes)

    def get_area_code(self):

        if not self.partner.phone:
            # Robustness in case of None
            return ''

        code = self.partner.phone.replace('(', '').replace(')', '')
        code = code.replace('-', '').strip()

        if code[0] == '1':
            code = code[1:4]
        else:
            code = code[:3]

        if len(code.strip()) == 3:
            return code

        return ''

    def get_xis_data(self):

        # Validate data. Must be a dealer.
        p = self.partner

        if not p.code or not p.is_company or not self.dealer:
            return ''

        market = self.dealer.market and self.dealer.market.name.lower()

        dealers = {
            'address': p.street or '',
            'buyit': 'false',
            'callsource_tollfree': self.dealer.callsource_tollfree or '',
            'city': p.city or '',
            'corpcontracts': '',  # p.pin
            'corpname': p.name or '',
            'country': p.country_id and p.country_id.name or '',
            'customermask': self.get_customermasks() or '',
            'dayspastdue': '',  # p.dayspastdue
            'dealerarea': self.get_dealerarea(),
            'dealercode': p.code.strip() or '',
            'dealeremail': '',  # must go from xis to OE.
            'dealername': p.name.strip() or '',
            'dealerurle': p.website or '',
            'dealerurlf': self.dealer.website_french or '',
            'dpd_override': '',  # '%s 00:00:00' % (p.dpd_override,)
            'fax': p.fax or '',
            'geolat': self.dealer.geolat,
            'geolon': self.dealer.geolon,
            #'isdealer': isdealer, # Deprecated
            #'ismember': ismember, # Deprecated

            # force to take 'en' of 'en_US'
            'language': p.lang and p.lang[:2] or '',
            'lastmoddate': self.get_last_modif_date(),
            'makes': self.get_xis_makes(),
            'market': market or '',
            'membertype': self.get_member_type() or '',
            'newemail': '',  # This field must go from xis to OE.
            'owner': self.dealer.owner or '',
            'owneremail': self.dealer.owneremail or '',

            'phone': p.phone or '',
            'phone2': p.mobile or '',
            'portalmask': self.get_portalmask() or '',
            'postalcode': self.partner.zip or '',
            'province': self.get_state(),
            'quoteflag': self.dealer.quoteflag and 'true' or 'false',
            'responsible': self.dealer.responsible or '',
            'salesguy': self.get_salesrep_ext_id() or '',
            'sitetype': self.get_site_type() or '',
            'tollfree': self.dealer.tollfree or '',
            'ttr': 'false',  # p.ttr_access and 'true' or 'false'

            'usedemail': '',
            'user10': self.dealer.user10 or '',
            'user12': self.dealer.user12 or '',
            'user12e': self.dealer.user12e or '',
            'user40': self.dealer.user40 or '',
            'user40e': self.dealer.user40e or '',
            'user80': self.dealer.user80 or '',
        }

        data = {
            "dealers": [dealers],
            "honeypot_cedric": 'Metallica Rules',  # security key
        }

        return data

    def process_response(self, dct_response):
        """
        If call is successful, updates categories if they have changed
        """

        xis_status = super(DealerRequest, self).process_response(
            dct_response)

        if not xis_status:
            return xis_status

        new_categories = set([cat.id for cat in self.partner.category_id])

        if (
            self.old_categories is None
            or new_categories == self.old_categories
        ):
            return xis_status

        PartnerCategoryRelRequest(
            self.partner,
            add_id=new_categories - self.old_categories,
            rem_id=self.old_categories - new_categories).execute()

        return xis_status


class PartnerCertificationRequest(XISRequestWrapper):

    model_xis = "XisDealerGroupDescUpdater"
    page_name = "dealer_groups_sf.spy"

    def __init__(self, parent):
        super(PartnerCertificationRequest, self).__init__(parent)

        # pool
        translate = parent.env['ir.translation']
        self.lst_desc = translate.search([
            ('name', '=',
                'xpr_xis_connector.dealer.certification,description'),
            ('res_id', '=', parent.id)])

        # model
        self.partner_category = parent.category

    def get_xis_data(self):
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
        self, parent, add_id=None, rem_id=None
    ):
        super(PartnerCategoryRelRequest, self).__init__(parent)

        self.add_id = add_id or set()
        self.rem_id = rem_id or set()

        # pool
        self.partner_cat_pool = parent.env["res.partner.category"]

        # model
        self.partner = parent

    def get_groups(self, group_ids):
        pcp = self.partner_cat_pool

        def is_group_root(tag):
            # Determines if tag is group parent.
            if tag.name == 'Group' and tag.parent_id.name == 'Dealer':
                return True

            return False

        for rec in pcp.browse(group_ids):

            if (
                rec.parent_id.name in ['Automatic', 'Manual'] and
                rec.parent_id.parent_id.name == 'Certification'
            ):
                # Certification

                yield {
                    'name': rec.name,
                    'grouptype': "{certification} {certification_root}".format(
                        certification=rec.parent_id.name,
                        certification_root=rec.parent_id.parent_id.name),
                }

                continue

            if (
                rec.parent_id.name == 'Association'
                and rec.parent_id.parent_id.name == 'Dealer'
            ):
                yield {
                    'name': rec.name,
                    'grouptype': "Dealer Association"
                }

                continue

            if is_group_root(rec.parent_id):
                yield {
                    'name': rec.name,
                    'grouptype': "Primary Group"
                }

                continue

            if is_group_root(rec.parent_id.parent_id):
                # Sub group. In XIS, this corresponds to two groups.

                yield {
                    'name': rec.parent_id.name,
                    'grouptype': "Primary Group"
                }

                yield {
                    'name': rec.name,
                    'grouptype': "Dealer Sub-Group"
                }

                continue

            # Default. Marketing Association.

            yield {
                'name': rec.name,
                'grouptype': rec.parent_id.name
            }

    def get_xis_data(self):
        # validate data

        if not self.partner.is_company or not self.partner.code:
            return None

        lst_group_add = [
            {
                'dealercode': self.partner.code,
                'name': rec['name'],
                'grouptype': rec['grouptype'],
            } for rec in self.get_groups(self.add_id)
        ]

        lst_group_rem = [
            {
                'dealercode': self.partner.code,
                'name': rec['name'],
                'grouptype': rec['grouptype'],
            } for rec in self.get_groups(self.rem_id)
        ]

        data = {
            "to_add": lst_group_add,
            "to_remove": lst_group_rem,
            "honeypot_roger": '1',  # security key
        }

        return data
