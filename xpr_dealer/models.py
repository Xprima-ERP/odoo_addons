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


class Dealer(models.Model):
    """
    Additional Parnter data.
    Mandatory for EVOLIO dealers.
    """

    # Extracted from res.partner
    _name = 'xpr_dealer.dealer'

    def _convert_ids_to_make_names(
        self, cr, uid, model_name, ids, context=None
    ):
        '''
        convert a list of ids to a list on make names.
        '''
        partner_make_obj = self.pool.get(model_name)
        makes_names = partner_make_obj.browse(
            cr, uid, ids, context=context)
        return [make.name for make in makes_names]

    def onchange_makes(
        self, cr, uid, ids,
        makes_car,
        makes_moto,
        makes_atv,
        makes_watercraft,
        makes_snowmobile,
        context=None
    ):
        split_char = ','
        makes_widget = {
            'partner_make_car': makes_car,
            'partner_make_moto': makes_moto,
            'partner_make_atv': makes_atv,
            'partner_make_watercraft': makes_watercraft,
            'partner_make_snowmobile': makes_snowmobile,
        }

        for _id in ids:
            make_names = []
            for _model_name, _widget in makes_widget.items():
                widget = _widget[0]
                make_ids = widget[2]
                make_names.extend(self._convert_ids_to_make_names(
                    cr,
                    uid,
                    _model_name,
                    make_ids))

            s_make_names = Set(make_names)
            partner = self.browse(cr, uid, _id)
            xis_makes = []
            if partner.xis_makes:
                str_xis_makes = partner.xis_makes
                xis_makes = str_xis_makes.split(split_char)
            s_xis_makes = Set(xis_makes)

            # Check if we need to remove or add to xis_makes.
            # If make_names has mode elements than xis_makes its and add.
            # Else it's a remove.
            if len(s_make_names) > len(xis_makes):
                s_make_names.difference_update(xis_makes)
                xis_makes.extend(s_make_names)
            else:
                s_xis_makes.difference_update(s_make_names)
                for make in s_xis_makes:
                    xis_makes.remove(make)
            vals = {'xis_makes': split_char.join(xis_makes)}
            self.write(cr, uid, _id, vals)
        return {'value': {}, 'domain': {}}

    def onchange_customer_of(self, cr, uid, ids, customermask_ids):
        value = {}
        value['is_member'] = False
        if customermask_ids:
            is_customer_of_auto123 = 1 in customermask_ids[0][2]
            if is_customer_of_auto123:
                value['is_member'] = True
        return {'value': value, 'domain': {}}

    def _sel_func_business_relationship(self, cr, uid, context=None):
        obj = self.pool.get("partner_business_relationship")
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ["name", "id"], context)
        res = [(r["id"], r["name"]) for r in res]
        return res

    def _sel_func_industry(self, cr, uid, context=None):
        obj = self.pool.get('partner_industry')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['name', 'id'], context)
        res = [(r['id'], r['name']) for r in res]
        return res

    def _sel_func_market(self, cr, uid, context=None):
        obj = self.pool.get('partner_market')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['name'], context)
        res = [(r['name'], r['name']) for r in res]
        return res

    def _sel_func_region(self, cr, uid, context=None):
        obj = self.pool.get('partner_region')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['name'], context)
        res = [(r['name'], r['name']) for r in res]
        return res

    partner = fields.One2many(
        'res.partner',
        'dealer',
        string="Related partner"
    )

    corpname = fields.Char("Legal Name", size=128)

    quoteflag = fields.Boolean("Send Quotes")
    responsible = fields.Char("Responsible", size=80)
    tollfree = fields.Char("Toll Free Number", size=64)
    callsource_tollfree = fields.Char("Evolio Call Tracking", size=64)
    geolat = fields.Float("GEO Latitude", digits=(6, 6))
    geolon = fields.Float("GEO Longitude", digits=(6, 6))

    billing_street = fields.Char(
        "Billing Street",
        size=128,
        required=False)

    # Unused. Kept because there is a street2 field.
    billing_street2 = fields.Char(
        "Billing Street2",
        size=128,
        required=False)

    billing_city = fields.Char("Billing City", size=128, required=False)
    billing_state_id = fields.Many2one(
        "res.country.state",
        "Billing State")

    billing_zip = fields.Char("ZIP Billing", size=24, required=False)

    billing_country_id = fields.Many2one(
        "res.country",
        "Billing Country")

    # TODO: Make 'website' translatable.
    website_french = fields.Char(
        "Website French", size=254, help="Website of Partner or Company")

    additional_website = fields.Char("Additional Website", size=254)

    # TODO: port to categories
    # 'xis_makes': fields.char('XIS Makes', size=254),

    makes = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_make_rel',
        string="Makes",
        #domain=[('id', 'child_of', self.env.ref('category_dealer_car'))]
    )

    industries = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_industry_rel',
        string="Industries",
        #domain=[('id', 'child_of', self.env.ref('category_dealer_car'))]
    )
    #####################################################
    # Editable manual fields. Selections or multi select.
    # Import these as partner categories

    # business_relationship_id = fields.Many2one(
    #     "partner_business_relationship",
    #     "Business Relationship",
    #     selection=_sel_func_business_relationship
    #     required=False)

    # customermask_ids = fields.Many2many(
    #     "customermask",
    #     "partner_customermask_rel",
    #     "partner_id",
    #     "customermask_id",
    #     "Customer of")

    # Looks like a field that can be deduced
    # portalmask = fields.Many2many(
    #     "partner_portalmask",
    #     "partner_partner_portalmask_rel",
    #     "partner_id",
    #     "partner_portalmask_id",
    #     "Used Cars On")

    # Doesn't seem to be used very much.
    # telephone_choice_id = fields.Many2one(
    #     "partner_telephone_choice",
    #     "Phone Choice")

    # Should not port. Data is not reliable.
    # categorization_field_id = fields.Many2one(
    #     "partner_categorization_field",
    #     "Categorization Field")

    # Not used often
    # membertype = fields.Many2many(
    #     "partner_business_type",
    #     "partner_partner_business_type_rel",
    #     "partner_id",
    #     "partner_business_type_id",
    #     "Business Types")

    # Not used often
    # industry_id = fields.Many2one(
    #     "partner_industry",
    #     "Industry",
    #     selection=_sel_func_industry,
    #     required=False)

    # Not used often
    # market = fields.Selection(_sel_func_market, "Market")

    # Not used often
    # region = fields.Selection(_sel_func_region, "Region")

    # Not used often
    # site_type_id = fields.Many2one("partner_site_type", "Site Type")


class Partner(models.Model):

    _inherit = "res.partner"

    dealer = fields.Many2one(
        'xpr_dealer.dealer',
        string='Dealer Info',
        ondelete='cascade')

    # 'xis_dc': fields.char('XIS dealer code', size=254),
    code = fields.Char('Code', size=254)  # Required for companies. Unique.

    # "is_dealer": fields.boolean("Is Dealer"),  # TODO: Calculate
    # "is_member": fields.boolean("Is Member"),  # TODO: Calculate

    _sql_constraints = [
        (
            'uniq_code',
            'unique(code)',
            "A code already exists with this name. Code must be unique."
        ),
    ]
