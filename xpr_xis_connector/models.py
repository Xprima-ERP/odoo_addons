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


class DealerCategoryMixin():
    """
    Common code for Dealer category extensions
    """

    _inherits = {
        'res.partner.category': 'category'
    }

    def _get_name(self):
        for dealer_cat in self:
            dealer_cat.name = dealer_cat.category.name

    def create(self, cr, uid, vals, context=None):
        status = super(PartnerCategory, self).create(
            cr, uid, vals, context=context)

        req = xis_request.PartnerCategoryRequest(
            self, cr, uid, status, context=context)

        req.execute()

        return status

    def write(self, cr, uid, ids, vals, context=None):
        status = super(PartnerCategory, self).write(
            cr, uid, ids, vals, context=context)

        if type(ids) is long or type(ids) is int:
            ids = [ids]

        for id_r in ids:
            req = xis_request.PartnerCategoryRequest(
                self, cr, uid, id_r, context=context)

            req.execute()

        return status

    name = fields.Char(compute=_get_name)


class DealerRegion(models.Model, DealerCategoryMixin):
    """
    Extension of a category, that permits
    to describe region for a dealer
    """

    _name = 'xpr_xis_connector.dealer.region'

    # TODO: Find a way to move this in mixin
    category = fields.Many2one(
        'res.partner.category',
        string="Category",
        required=True,
        ondelete='cascade',
        domain="[('parent_id.name', '=', 'Region')]",
    )

    # Region code
    region_code = fields.Char('Region Code')


class DealerCertification(models.Model, DealerCategoryMixin):
    """
    Extension of a category, that permits
    to describe certifications for a dealer
    """

    _name = 'xpr_xis_connector.dealer.certification'

    # TODO: Find a way to move this in mixin
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

    def _get_code(self):
        for dealer in self:
            dealer.xis_dc = dealer.code

    xis_makes = fields.Char(compute=_get_xis_makes)

    area_code = fields.Char(size=3, compute=_get_area_code)

    # xis_dc redirects to 'code'
    xis_dc = fields.Char(compute=_get_code)


class SaleOrder(models.Model):
    """
    Takes care of synching the xis_guote_id from XIS with the client_order_ref
    """

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
            xis_val["client_order_ref"] = qt_xisid
            super(SaleOrder, self).write(
                cr, uid, status, xis_val, context=context)

        return status

    def write(self, cr, uid, ids, vals, context=None):
        status = super(SaleOrder, self).write(
            cr, uid, ids, vals, context=context)

        for r_id in ids:
            is_new = False
            xis_val = {}
            qt_xisid = self.browse(
                cr, uid, r_id, context=context).client_order_ref

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
                    xis_val["client_order_ref"] = qt_xisid
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


class Partner(models.Model):
    """
    Synchs partner categories
    """
    _inherit = "res.partner"

    def create(self, cr, uid, vals, context=None):
        status = super(Partner, self).create(
            cr, uid, vals, context=context)

        if self.browse(cr, uid, status, context=context).customer:
            req = xis_request.PartnerRequest(
                self, cr, uid, status, context=context)

            req.execute()

            dct_cat_vals = vals.get("category_id")
            if dct_cat_vals:
                lst_new_cat = [cat[2] for cat in dct_cat_vals][0]
                req = xis_request.PartnerCategoryRelRequest(
                    self, cr, uid, status, context=context,
                    add_id=lst_new_cat)

                req.execute()

        return status

    def write(self, cr, uid, ids, vals, context=None):
        # Only the manager of the modifier can change
        # the user_id of this partner

        if 'user_id' in vals:
            authorized_modifiers_groups = [
                'Helpdesk / Agent',
                'Administration / Settings',
                'Sales / Manager',
                'Contact Creation',
            ]

            users_obj = self.pool.get('res.users')
            writer_user = users_obj.browse(cr, uid, uid)
            user_groups = [group.full_name for group in writer_user.groups_id]
            is_authorized = False

            for group in authorized_modifiers_groups:
                if group not in user_groups:
                    continue

                if group != u'Sales / Manager':
                    # This looks like a recent update.
                    # Should update
                    continue

                # Need to be the manager of the user_id
                # or the coach.

                hr_emp_obj = self.pool.get('hr.employee')
                partner = self.browse(cr, uid, ids[0])
                s_args = [('user_id', '=', partner.user_id.id)]
                try:
                    user_id_hr = hr_emp_obj.search(
                        cr,
                        uid,
                        s_args,
                        context=context)[0]

                except IndexError:
                    continue

                user_hr = hr_emp_obj.browse(
                    cr,
                    uid,
                    user_id_hr,
                    context)

                manager_hr = user_hr.parent_id
                coach_hr = user_hr.coach_id

                if manager_hr and uid == manager_hr.user_id.id:
                    is_authorized = True
                    break

                if coach_hr and uid == coach_hr.user_id.id:
                    is_authorized = True
                    break

                if partner.user_id and uid == partner.user_id.id:
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
                req = xis_request.PartnerRequest(
                    self, cr, uid, id_r, context=context)

                req.execute()

                if dct_cat_vals:
                    # add rel to dealer_group
                    new_cat = lst_new_cat[i]
                    old_cat = lst_old_cat[i]
                    # diff dealergroup
                    rem_cat = [x for x in old_cat if x not in set(new_cat)]
                    add_cat = [x for x in new_cat if x not in set(old_cat)]
                    req = xis_request.PartnerCategoryRelRequest(
                        self, cr, uid, id_r,
                        context=context,
                        add_id=add_cat,
                        rem_id=rem_cat)

                    req.execute()

            i += 1

        return status


class Product(models.Model):
    """
    Contains fields to expose dealers data for XIS updates.
    At the last update, the remaining fields are actually duplicates.
    This class could be deprecated.
    """

    _inherit = "product.template"

    def _get_code(self):
        for p in self:
            p.xis_product_code = p.default_code

    xis_product_code = fields.Char(
        'XIS product code', size=30, compute=_get_code)
