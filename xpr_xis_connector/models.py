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


import time
import json
import utils
import xis_request
from openerp import models, fields, api
from openerp.tools.translate import _
from sets import Set


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

    @api.multi
    def write(self, vals):
        status = super(DealerRegion, self).write(vals)

        for region in self:
            xis_request.PartnerRegionRequest(region).execute()

        return status

    @api.model
    def create(self, vals):

        region = super(DealerRegion, self).create(vals)

        xis_request.PartnerRegionRequest(region).execute()

        return region

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

        status = super(DealerCertification, self).write(vals)

        for certification in self:
            xis_request.PartnerCertificationRequest(certification).execute()

        return status

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


class Dealer(models.Model):
    """
    Contains fields to expose dealers data for XIS updates.
    At the last update, the remaining fields are actually duplicates.
    This class could be deprecated.
    """

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

    # xis_dc redirects is now 'code'
    xis_makes = fields.Char(compute=_get_xis_makes)

    area_code = fields.Char(size=3, compute=_get_area_code)


class SaleOrder(models.Model):
    """
    Takes care of synching the client_order_ref with the XIS xis_quote_id
    """

    _inherit = "sale.order"

    @api.multi
    def write(self, vals):
        """
        If order ref is not initialized yet, get one from XIS and repair it.
        """

        status = super(SaleOrder, self).write(vals)

        for order in self:

            if order.client_order_ref:
                continue

            xis_request.SaleOrderRequest(
                order, is_update=True).execute()

        return status

    @api.model
    def create(self, vals):
        """
        Upon creation, get reference from XIS
        """
        order = super(SaleOrder, self).create(vals)

        xis_request.SaleOrderRequest(order).execute()

        return order


class Partner(models.Model):
    """
    Synchs partner categories
    """
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        """
        Upon creation, updates XIS with new partner and its groups
        """
        partner = super(Partner, self).create(vals)

        xis_request.PartnerRequest(partner, set()).execute()

        return partner

    @api.multi
    def write(self, vals):
        """
        Upon update, updates XIS with new fields and groups
        """

        if 'user_id' in vals:
            # Check if user may be updated
            for partner in self:
                if not self.may_change_user(partner):
                    # At least one partner may not be updated
                    del vals['user_id']
                    break

        # Keep track of old category values if needed
        lst_old_cat = dict()

        dct_cat_vals = vals.get("category_id")

        if dct_cat_vals:
            for partner in self:
                lst_old_cat[partner.id] = set([
                    cat.id for cat in partner.category_id
                ])

        # Make the standard call
        status = super(Partner, self).write(vals)

        # Update XIS with new fields and categories
        for partner in self:
            if not partner.customer:
                continue

            xis_request.PartnerRequest(
                partner, dct_cat_vals.get(partner.id)).execute()

        return status

    def may_change_user(self, partner):
        """
        Write helper function. Determines
        if user may be updated within context
        """

        # Only the manager of the modifier can change
        # the user_id of this partner

        authorized_modifiers_groups = set([
            #'Helpdesk / Agent',
            #'Administration / Settings',
            'Sales / Manager',
            #'Contact Creation',
        ])

        writer_user = self.env.user
        user_groups = set([group.full_name for group in writer_user.groups_id])

        for group in authorized_modifiers_groups & authorized_modifiers_groups:

            # Need to be the manager of the user_id
            # or the coach.

            hr_emp_obj = self.env['hr.employee']
            s_args = [('user_id', '=', partner.user_id.id)]
            try:
                user_id_hr = hr_emp_obj.search(s_args)[0]
            except IndexError:
                continue

            user_hr = hr_emp_obj.browse(user_id_hr)
            manager_hr = user_hr.parent_id
            coach_hr = user_hr.coach_id

            if (
                (manager_hr and uid == manager_hr.user_id.id)
                or (coach_hr and uid == coach_hr.user_id.id)
                or (partner.user_id and uid == partner.user_id.id)
            ):
                return True

        return False


class User(models.Model):
    _inherit = "res.users"

    xis_user_external_id = fields.Integer('XIS external user', required=True)
