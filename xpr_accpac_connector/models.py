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

    idcust = fields.Char(string="IDCust", size=50)

    namecust = fields.Char(string="NameCust", size=254)

    # If not DEALER, we do not care for now
    idgrp = fields.Char(string="IdGrp", size=50)

    dateinac = fields.Date(string="DateInac")  # Inactive??
    datestart = fields.Date(string="DateStart")  # ??
    datelastmn = fields.Date(string="DateLastMN")  # ??

    # Should be no more than one match, based on dealercode
    dealercode = fields.Char(string="Dealer Code", size=50)
    mapped = fields.Boolean(strong="Is Mapped")  # Map is confirmed.
    partner = fields.Many2one(
        'res.partner',
        'Partner',
    )


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

    date = fields.Date(string="Date")
    idcust = fields.Char(string="Customer#", size=50)
    idinvoice = fields.Char(string="Invoice#", size=50)
    iditem = fields.Char(string="Item#", size=50)

    amount = fields.Float(string='Amount', digits=(6, 2), default=0)

    # Based on customer match
    partner = fields.Many2one(
        'res.partner',
        'Partner',
        readonly=True
    )

    mapped = fields.Boolean(strong="Is Mapped")


class ClientProcess(models.TransientModel):

    """
    Dealer Assign wizard.

    Loaded to assign a sales person to multiple dealers
    """

    _name = 'xpr_accpac_connector.client_process'

    def _init_clients(self):

        context = self.env.context

        active_ids = context.get('active_ids')

        if not active_ids:
            return []

        return self.env['xpr_accpac_connector.client'].browse(active_ids)

    def _init_count(self):

        context = self.env.context

        active_ids = context.get('active_ids')

        if not active_ids:
            return 0

        return len(active_ids)

    clients = fields.Many2many(
        'xpr_accpac_connector.client',
        'clients_assign_clients_rel',
        string='Clients',
        required=True,
        default=_init_clients)

    count = fields.Integer("Selected clients", default=_init_count)

    @api.multi
    def process_import(self):

        mapped_ids = set()

        # Kill duplicate optional values
        for value in self.env['xpr_accpac_connector.clientoptionalvalue'].search([]):
            key = (value.idcust, value.optfield)

            if key in mapped_ids:
                # Kill duplicate
                value.unlink()
            else:
                mapped_ids.add(key)

        # Kill duplicates of unmarked entries

        mapped_ids = set()
        for client in self.clients:

            if client.mapped:
                continue

            key = client.idcust

            if key in mapped_ids:
                # Kill duplicate
                client.unlink()
            else:
                mapped_ids.add(key)

        # Mark mapped clients

        mapped_ids = set([
            client.idcust for client
            in self.env['xpr_accpac_connector.client'].search([('mapped', '=', True)])
        ])

        for client in self.clients:

            if not client.partner or client.mapped:
                continue

            if client.idcust in mapped_ids:
                # Alread mapped. Kill duplicate.
                client.unlink()
                continue

            mapped_ids.add(client.idcust)
            client.mapped = True

        # Map partner
        for client in self.clients:

            if client.idcust in mapped_ids and not client.mapped:
                client.unlink()
                continue

            code = self.env['xpr_accpac_connector.clientoptionalvalue'].search([
                ('idcust', '=', client.idcust), ('optfield', '=', 'DEALERCODE')])

            if not code:
                client.partner = None
                continue

            client.dealercode = code.value

            partner = self.env['res.partner'].search(
                [('code', '=', code.value)])

            if not partner:
                client.partner = None
                continue

            client.partner = partner


class InvoiceProcess(models.TransientModel):

    """
    Dealer Assign wizard.

    Loaded to assign a sales person to multiple dealers
    """

    _name = 'xpr_accpac_connector.invoice_process'

    def _init_lines(self):

        context = self.env.context

        active_ids = context.get('active_ids')

        if not active_ids:
            return []

        return self.env['xpr_accpac_connector.invoiceline'].browse(active_ids)

    def _init_count(self):

        context = self.env.context

        active_ids = context.get('active_ids')

        if not active_ids:
            return 0

        return len(active_ids)

    lines = fields.Many2many(
        'xpr_accpac_connector.invoiceline',
        'invoice_assign_clients_rel',
        string='Lines',
        required=True,
        default=_init_lines)

    count = fields.Integer("Selected lines", default=_init_count)

    @api.multi
    def process_import(self):

        # Kill duplicates of unmarked entries

        mapped_ids = set([
            (line.idcust, line.idinvoice, line.iditem) for line
            in self.env['xpr_accpac_connector.invoiceline'].search([('mapped', '=', False)])
        ])

        for line in self.lines:

            key = (line.idcust, line.idinvoice, line.iditem)

            if key in mapped_ids:
                # Mark as visited
                mapped_ids.remove(key)
            else:
                # Kill duplicate
                line.unlink()

        mapped_ids = set([
            (line.idcust, line.idinvoice, line.iditem) for line
            in self.env['xpr_accpac_connector.invoiceline'].search([('mapped', '=', True)])
        ])

         # Mark mapped lines
        for line in self.lines:

            if line.mapped:
                continue

            if (line.idcust, line.idinvoice, line.iditem) in mapped_ids:
                # Alread mapped. Kill duplicate.
                line.unlink()
                continue

            if line.partner:
                # New map
                mapped_ids.add((line.idcust, line.idinvoice, line.iditem))
                line.mapped = True

        # Map lines
        for line in self.lines:

            client = self.env['xpr_accpac_connector.client'].search([
                ('idcust', '=', line.idcust), ('mapped', '=', True)])

            if client:
                line.partner = client.partner
            else:
                # This should never happen. Customer removed??
                line.partner = None
                line.mapped = False
