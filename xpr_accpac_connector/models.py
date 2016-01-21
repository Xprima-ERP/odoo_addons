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

    # dateinac = fields.Date(string="DateInac")  # Inactive??
    # datestart = fields.Date(string="DateStart")  # ??
    # datelastmn = fields.Date(string="DateLastMN")  # ??

    # Should be no more than one match, based on dealercode
    dealercode = fields.Char(string="Dealer Code", size=50)
    mapped = fields.Boolean(string="Is Mapped")  # Map is confirmed.
    partner = fields.Many2one(
        'res.partner',
        'Partner',
    )

    @api.one
    def merge_into(self, target):
        # Copy import data not part of the key.
        # TODO: Add adress when it is available in model

        target.namecust = self.namecust
        target.idgrp = self.idgrp
        #target.dateinac = self.idgrp
        #target.datestart = self.idgrp
        #target.datelastmn = self.idgrp

        self.unlink()


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

    # Result of previous import. Proper target for data merges
    mapped = fields.Boolean(string="Is Mapped")

    @api.one
    def merge_into(self, target):
        # Copy data. The key is the same already.
        target.value = self.value
        self.unlink()


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

    @api.one
    def merge_into(self, target):
        # Nothing to copy. Simply unlink.
        self.unlink()


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

    def _process_optional_values(self):
        """
        Takes care of processing optional values.
        Duplicate values are merged into one entry, current one if possible.
        """
        mapped_ids = dict([
            (value.id, (value.idcust, value.optfield))
            for value in self.env['xpr_accpac_connector.clientoptionalvalue'].search([
                ('mapped', '=', True)
            ])
        ])

        # Merge duplicate optional values

        for value in self.env['xpr_accpac_connector.clientoptionalvalue'].search(
            [('mapped', '=', False)]
        ):
            key = (value.idcust, value.optfield)

            if key in mapped_ids:
                # Merge duplicate
                value.merge_into(mapped_ids[key])
                continue

            # Optional values automatically map if no merge

            value.mapped = True
            mapped_ids[key] = value

    def _process_clients(self):
        """
        Duplicate clients are merged into one, current mapped one if possible.
        """

        mapped_ids = dict([
            (client.idcust, client) for client
            in self.env['xpr_accpac_connector.client'].search([('mapped', '=', True)])
        ])

        for client in self.clients:

            if client.mapped:
                continue

            key = client.idcust

            if key in mapped_ids:
                # Merge duplicate
                client.merge_into(mapped_ids[key])
                continue

            # Make available for merges

            mapped_ids[key] = client

            if client.partner:
                # Mark it. This is a confirmation that partner is good.
                client.mapped = True
                continue

            # Attempt to find partner.

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

    @api.multi
    def process_import(self):

        self._process_optional_values()
        self._process_clients()


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

        # Merge duplicates of unmarked entries

        mapped_ids = dict([
            ((line.idcust, line.idinvoice, line.iditem), line) for line
            in self.env['xpr_accpac_connector.invoiceline'].search([('mapped', '=', True)])
        ])

        for line in self.lines:

            if line.mapped:
                continue

            key = (line.idcust, line.idinvoice, line.iditem)

            if key in mapped_ids:
                # Merge
                line.merge_into(mapped_ids[key])
                continue

            # Make available for merges.
            mapped_ids[key] = line

            if line.partner:
                # Mark as confirmation that map is correct
                line.mapped = True
                continue

        # Map or remap lines to customer. Customer may have changed.

        mapped_ids = dict([
            (client.idcust, client) for client in
            self.env['xpr_accpac_connector.client'].search([
                ('idcust', 'in', [int(line.idcust) for line in self.lines]),
                ('mapped', '=', True)
            ])
        ])

        for line in self.lines:

            key = line.idcust

            if line.idcust in mapped_ids:
                line.partner = mapped_ids[key].partner
            else:
                # This should never happen. Customer removed??
                line.partner = None
                line.mapped = False


class Partner(models.Model):
    _inherit = 'res.partner'

    accpac_source = fields.One2many(
        'xpr_accpac_connector.client',
        'partner')
