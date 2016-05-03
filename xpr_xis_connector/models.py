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

import xis_request
from openerp import models, fields, api
from openerp.tools.translate import _


class PartnerCategory(models.Model):
    """
    Adds accessor fields to get XIS extensions for categories
    """
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


class DealerRegion(models.Model):
    """
    Extension of a category, that permits
    to describe region for a dealer
    """

    _inherits = {
        'res.partner.category': 'category'
    }

    _name = 'xpr_xis_connector.dealer.region'

    def _get_name(self):
        for dealer_cat in self:
            dealer_cat.name = dealer_cat.category.name

    name = fields.Char(compute=_get_name)

    category = fields.Many2one(
        'res.partner.category',
        string="Category",
        required=True,
        ondelete='cascade',
        domain="[('parent_id.name', '=', 'Region')]",
    )

    # Region code
    region_code = fields.Char('Region Code')


class DealerCertification(models.Model):
    """
    Extension of a category, that permits
    to describe certifications for a dealer
    """

    _name = 'xpr_xis_connector.dealer.certification'

    _inherits = {
        'res.partner.category': 'category'
    }

    def _get_name(self):
        for dealer_cat in self:
            dealer_cat.name = dealer_cat.category.name

    @api.multi
    def write(self, vals):

        super(DealerCertification, self).write(vals)

        for certification in self:
            xis_request.PartnerCertificationRequest(certification).execute()

    @api.model
    def create(self, vals):

        certification = super(DealerCertification, self).create(vals)
        xis_request.PartnerCertificationRequest(certification).execute()
        return certification

    name = fields.Char(compute=_get_name)
    description = fields.Text('Description', translate=True)

    category = fields.Many2one(
        'res.partner.category',
        string="Category",
        required=True,
        ondelete='cascade',
        domain=(
            "['|',('parent_id.name', '=', 'Automatic Certification'), "
            "('parent_id.name', '=', 'Manual Certification')]"
        ),
    )

    # Certification
    xis_certification_id = fields.Char('XIS Certification ID')


class SaleOrder(models.Model):
    """
    Takes care of synching the client_order_ref with the XIS xis_quote_id
    """

    _inherit = "sale.order"

    @api.multi
    def write(self, vals):
        """
        Syncs with XIS when contract is approved
        """

        super(SaleOrder, self).write(vals)

        # No need to feedback output fields or fields that have no effect in XIS.

        for key in ['client_order_ref']:
            if key in vals:
                vals.pop(key)

        if not vals:
            return

        for order in self:

            if order.state not in [
                'manager_approved',
                'contract_approved',
                'cancel',
                'lost',
                'sent',
                'done',
                'production',
            ]:
                # No need to synch before approval.
                continue

            xis_request.SaleOrderRequest(order).execute()


class Partner(models.Model):
    """
    Synchs partner categories
    """
    _inherit = "res.partner"

    def _pre_write(self, vals):
         # Keep track of old category values if needed
        lst_old_cat = dict()

        if vals.get("category_id"):
            for partner in self:
                lst_old_cat[partner.id] = set([
                    cat.id for cat in partner.category_id
                ])

        return lst_old_cat

    def _post_write(self, lst_old_cat):
        # Update XIS with new fields and categories
        # For dealers only.
        for partner in self:
            if not partner.customer or not partner.dealer:
                continue

            xis_request.DealerRequest(
                partner.dealer[0],
                old_categories=lst_old_cat.get(partner.id)
            ).execute()

    @api.multi
    def write(self, vals):
        """
        Upon update, updates XIS with new fields and groups
        """

        if self.env.context.get('no_xis_synch'):
            # Happens if this write is triggered Dealer.write
            return super(Partner, self).write(vals)

        post_write_data = self._pre_write(vals)

        # Make the standard call
        super(Partner, self).write(vals)

        self._post_write(post_write_data)


class Dealer(models.Model):
    """
    Contains fields to expose dealers data for XIS updates.
    At the last update, the remaining fields are actually duplicates.
    This class could be deprecated.
    """

    _inherit = 'xpr_dealer.dealer'

    @api.model
    def create(self, vals):
        """
        Upon creation, updates XIS with new partner and its groups
        """

        dealer = super(Dealer, self).create(vals)

        xis_request.DealerRequest(dealer).execute()

        return dealer

    def _pre_write(self, vals):
        # Copy of Partner method
        lst_old_cat = dict()

        if vals.get("category_id"):
            for partner in self:
                lst_old_cat[partner.id] = set([
                    cat.id for cat in partner.category_id
                ])

        return lst_old_cat

    def _post_write(self, lst_old_cat):
        for dealer in self:
            if not dealer.partner.customer:
                continue

            xis_request.DealerRequest(
                dealer,
                old_categories=lst_old_cat.get(dealer.id)
            ).execute()

    @api.multi
    def write(self, vals):

        post_write_data = self._pre_write(vals)

        # Make the standard call
        super(Dealer, self.with_context(no_xis_synch=True)).write(vals)

        for key in ['assigned_user']:
            if key in vals:
                vals.pop(key)

        if not vals:
            return

        self._post_write(post_write_data)


class User(models.Model):
    _inherit = "res.users"

    xis_user_external_id = fields.Integer('XIS external user', required=True)
