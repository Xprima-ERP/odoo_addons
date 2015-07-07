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


class XisRequest():

    """
    Class to send request to XIS software. Using POST http request.
    """

    def __init__(self, _logger, cr, uid, parent):
        self.debug = True
        self._logger = _logger
        self.cr = cr
        self.uid = uid
        self.parent = parent
        self.param_pool = parent.pool.get('ir.config_parameter')

    def send_request(self, model, url, values):
        """
        Send POST request to giving url (if not contain GET request).
        Send an email if request contain error.
        Return (status, output)
        """
        status = False
        result = None
        response = None
        self._logger.debug(values)
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
                if  re_encode and value:
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
        self._logger.debug(data)

        # check configuration to active XIS connector
        is_enable = False

        lst_param = self.param_pool.search(self.cr, self.uid,
                                           [('key', '=',
                                             'xis.enable.connector')])
        if lst_param:
            param = self.param_pool.browse(self.cr, self.uid,
                                           lst_param[0]).value
            if param and (param == "1" or param.lower() == "true"):
                is_enable = True

        if not is_enable:
            self._logger.debug("xis.enable.connector is false.")
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
                self._logger.error('We failed to reach a server. Reason: %s' %
                                   e.reason)
            elif hasattr(e, 'code'):
                msg = 'The server couldn\'t fulfill the request. ' \
                      'Error code: %s' % code
                self._logger.error(msg)
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
        self._logger.debug(result)
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
