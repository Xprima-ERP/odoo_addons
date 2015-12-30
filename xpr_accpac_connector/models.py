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

from openerp import models, fields, api
from openerp.tools.translate import _


class Client(models.Model):
    """
    AccPac client optional value import.
    Used to link customer ids to dealer codes
    """

    _name = 'xpr_accpac_connector.client'

    @api.depends('idcust')
    def _get_partner(self):
        for client in self:
            code = self.env['xpr_accpac_connector.clientoptionalvalue'].search(
                [('optfield', '=', 'DEALERCODE'), ('idcust', '=', client.idcust)])

            if not code:
                client.partner = None
                continue

            partner = self.env['xpr_accpac_connector.clientoptionalvalue'].search(
                [('code', '=', code.value)])

            if not partner:
                # Dealercode might not match. Typo?
                client.partner = None
                continue

            client.partner = partner

    idcust = fields.Char(string="IDCust", size=50)

    namecust = fields.Char(string="NameCust", size=254)

    # If not DEALER, we do not care for now
    idgrp = fields.Char(string="IdGrp", size=50)
    dateinac = fields.Date(string="DateInac")  # Inactive??
    datestart = fields.Date(string="DateStart")  # ??
    datelastmn = fields.Date(string="DateLastMN")  # ??

    # Should be no more than one match, based on dealercode
    partner = fields.Many2one(
        'res.partner',
        'Partner',
        readonly=True, _compute=_get_partner, store=True)

    _sql_constraints = [
        (
            'uniq_idcust',
            'unique(idcust)',
            "A customer already exists with this id. Cust ID must be unique."
        ),
    ]


class ClientOptionalValue(models.Model):
    """
    AccPac client optional value import.
    Used to link customer ids to dealer codes
    """

    # Extracted from res.partner
    _name = 'xpr_accpac_connector.clientoptionalvalue'

    idcust = fields.Char(string="IDCust", size=50)

    # If not DEALERCODE, then we don't really care
    optfield = fields.Char(string="OptField", size=254)

    # Meaning of this field depends on optfield
    value = fields.Char(string="Value", size=254)


class InvoiceLine(models.Model):
    """
    AccPac Invoice line import.
    Used to determine if used is being billed.
    Eventually, may be used to import Invoices.
    """

    _name = 'xpr_accpac_connector.invoiceline'

    @api.depends('idcust')
    def _get_partner(self):
        for line in self:

            client = self.env['xpr_accpac_connector.client'].search([('idcust', '=', line.idcust)])

            if client:
                line.partner = client.partner
            else:
                line.partner = None

    date = fields.Date(string="Date")
    idcust = fields.Char(string="Customer#", size=50)
    idinvoice = fields.Char(string="Invoice#", size=50)
    iditem = fields.Char(string="Item#", size=50)

    amount = fields.Float(string='Amount', digits=(6, 2), default=0)

    # Should be no more than one match, based on customer match
    partner = fields.Many2one(
        'res.partner',
        'Partner',
        readonly=True, _compute=_get_partner, store=True)
