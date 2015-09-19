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


class Partner(models.Model):

    _inherit = "res.partner"

    dealer = fields.One2many(
        'xpr_dealer.dealer',
        'partner',
        string='Dealer Info'
        )
    # 'xis_dc': fields.char('XIS dealer code', size=254),
    code = fields.Char('Code', size=254)  # Required for companies. Unique.

    # TODO: dealer != null
    # "is_dealer": fields.boolean("Is Dealer"),

    # TODO: has 'Auto123' in customer
    # "is_member": fields.boolean("Is Member"),

    _sql_constraints = [
        (
            'uniq_code',
            'unique(code)',
            "A code already exists with this name. Code must be unique."
        ),
    ]


class Dealer(models.Model):
    """
    Additional Parnter data.
    Mandatory for EVOLIO dealers.
    """

    # Extracted from res.partner
    _name = 'xpr_dealer.dealer'
    _inherits = {
        'res.partner': 'partner'
    }

    partner = fields.Many2one(
        'res.partner',
        string="Related partner",
        required=True,
        ondelete='cascade'
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

    # TODO: port to categories. Order of makes is important for XIS
    # 'xis_makes': fields.char('XIS Makes', size=254),

    # Industry translations
    #     en
    #  New Car
    #  Used Car
    #  New Moto
    #  Used Moto
    #  New ATV
    #  Used ATV
    #  New Snowmobile
    #  Used Snowmobile
    #  New Watercraft
    #  Used Watercraft
    # fr
    #  Nouvelle voiture
    #  Voiture usagée
    #  Nouvelle moto
    #  Moto usagée
    #  Nouveau VTT
    #  VTT usagé
    #  Nouvelle motoneige
    #  Motoneige usagée
    #  Nouveau Véhicule marin
    #  Véhicule marin usagé

    makes = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_make_rel',
        string="Makes",
    )

    business = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_business_rel',
        string="Business",
    )

    # Old customermask
    customer = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_customer_rel',
        string="Customer Of",
    )

    # TODO: Make this field computable
    # business_relationship
    # "Prospect" "Existing Customer" "Past Customer"
