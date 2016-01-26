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

    is_test = fields.Boolean('Is Test') # Indicates if this is a test dealer.

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

    _defaults = {
        # No emails to customers by default
        'opt_out': True,
        'notify_email': 'none'
    }


class Users(models.Model):
    _inherit = "res.users"

    # Updates related dealers when active flag is updated
    # Called by automated action
    @api.one
    def _mark_dealers(self):
        for dealer in self.env['xpr_dealer.dealer'].search([('partner.user_id', '=', self.id)]):
            dealer.assigned_user = self.active


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
        ondelete='cascade',
        domain=[('is_company', '=', True)]
    )

    def onchange_state(self, *args, **kwargs):
        # TODO: Check if we need to call super class.
        pass

    ######## Mail API redirected to partner. TODO: Make a mixin out of this.

    def message_get_subscription_data(self, cr, uid, ids, user_pid=None, context=None):
        ids_map = dict([
            (dealer.id, dealer.partner.id) for dealer in self.browse(cr, uid, ids, context=context)
        ])

        res = self.pool.get('res.partner').message_get_subscription_data(
            cr, uid, ids_map.values(), user_pid=user_pid, context=context)

        # Replace partner id with dealer id in returned result
        return dict([(dealer_id, res[partner_id]) for (dealer_id, partner_id) in ids_map.items()])

    def message_get_suggested_recipients(self, cr, uid, ids, context=None):

        ids_map = dict([
            (dealer.id, dealer.partner.id) for dealer
            in self.pool.get('xpr_dealer.dealer').browse(cr, uid, ids, context=context)
        ])

        context['default_model'] = 'res.partner'
        context['default_res_id'] = self.pool.get('xpr_dealer.dealer').browse(
            cr, uid, [context['default_res_id']], context=context)[0].partner.id

        res = self.pool.get('res.partner').message_get_suggested_recipients(
            cr, uid, ids_map.values(), context=context)

        # Replace partner id with dealer id in returned result
        res = dict([(dealer_id, res[partner_id]) for (dealer_id, partner_id) in ids_map.items()])

        return res

    def _convert_to_list(self, thread_id):
        if type(thread_id) is list:
            return thread_id

        return [thread_id]

    def message_post(
        self, cr, uid, thread_id, body='', subject=None, type='notification',
        subtype=None, parent_id=False, attachments=None, context=None,
        content_subtype='html', **kwargs
    ):

        thread_id = self._convert_to_list(thread_id)

        thread_id = self.pool.get('xpr_dealer.dealer').browse(
            cr, uid, thread_id, context=context)[0].partner.id

        return self.pool.get('res.partner').message_post(
            cr, uid, thread_id, body=body, subject=subject, type=type,
            subtype=subtype, parent_id=parent_id, attachments=attachments, context=context,
            content_subtype=content_subtype, **kwargs)

    def message_subscribe_users(
        self, cr, uid, ids, user_ids=None, subtype_ids=None, context=None
    ):
        ids = [dealer.partner.id for dealer in self.browse(cr, uid, ids, context=context)]

        return self.pool.get('res.partner').message_subscribe_users(
            cr, uid, ids, user_ids=user_ids, subtype_ids=subtype_ids, context=context)

    def message_subscribe(self, cr, uid, ids, partner_ids, subtype_ids=None, context=None):
        ids = [dealer.partner.id for dealer in self.browse(cr, uid, ids, context=context)]

        return self.pool.get('res.partner').message_subscribe(
            cr, uid, ids, partner_ids, subtype_ids=subtype_ids, context=context)

    def message_unsubscribe_users(self, cr, uid, ids, user_ids=None, context=None):
        ids = [dealer.partner.id for dealer in self.browse(cr, uid, ids, context=context)]

        return self.pool.get('res.partner').message_unsubscribe_users(
            cr, uid, ids, user_ids=user_ids, context=context)

    def message_unsubscribe(self, cr, uid, ids, partner_ids, context=None):
        ids = [dealer.partner.id for dealer in self.browse(cr, uid, ids, context=context)]

        return self.pool.get('res.partner').message_unsubscribe(
            cr, uid, ids, partner_ids, context=context)

    def message_auto_subscribe(self, cr, uid, ids, updated_fields, context=None, values=None):
        ids = [dealer.partner.id for dealer in self.browse(cr, uid, ids, context=context)]

        return self.pool.get('res.partner').message_auto_subscribe(
            cr, uid, ids, updated_fields, context=context, values=values)

    def read_followers_data(self, cr, uid, follower_ids, context=None):

        return self.pool.get('res.partner').read_followers_data(
            cr, uid, follower_ids, context=context)

    ######## End of mail API

    @api.depends('user_id')
    def _assigned_user(self):
        for dealer in self:
            dealer.assigned_user = dealer.user_id and dealer.user_id.active

    @api.onchange('makes', 'make_sequence')
    def _check_ordered(self):
        for dealer in self:

            makes_set = set(m.name for m in dealer.makes)
            makes_parsed = (dealer.make_sequence or '').split(',')

            # Respect order of present makes
            new_makes = [m for m in makes_parsed if m in makes_set]

            dealer.make_sequence = ','.join(new_makes + list(makes_set - set(makes_parsed)))

    assigned_user = fields.Boolean(
        string="Assigned Salesperson",
        readonly=True,
        compute=_assigned_user,
        store=True)

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

    make_sequence = fields.Char('Make Sequence')

    business = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_business_rel',
        string="Business",
    )

    # Old customermask
    customer = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_customer_rel',
        string="Customer of",
    )

    # TODO: Make this field computable
    # business_relationship
    # "Prospect" "Existing Customer" "Past Customer"

    site_type = fields.Selection(
        [
            ("has_website_with_us", "Has Website With Us"),
            ("has_a_link_or_portals_to_their_site",
                "Has a link or portals to their site"),
            ("does_not_have_a_website", "Does not have a website")
        ],
        "Site Type"
    )

    telephone_choice = fields.Selection(
        [
            ("phone", "Phone"),
            ("toll_free", "Toll Free"),
            ("call_tracking", "Evolio Call")
        ],
        "Phone Choice"
    )

    region = fields.Many2one(
        'res.partner.category',
        string="Region",
    )

    portalmask = fields.Many2many(
        'res.partner.category',
        'dealer_partner_category_portal_rel',
        string="Used Cars On")

    market = fields.Many2one(
        'res.partner.category',
        string="Market",
    )

    owner = fields.Char(
        "Dealership Owner",
        size=45,
        help="This field is there for the synchronization to XIS")

    owneremail = fields.Char(
        "Dealership Owner Email",
        size=240,
        help="This field is there for the synchronization to XIS")

    user10 = fields.Char("User10", size=10)
    user12 = fields.Char("User12", size=12)
    user12e = fields.Char("User12e", size=12)
    user40 = fields.Char("User40", size=40)
    user40e = fields.Char("User40e", size=40)
    user80 = fields.Char("User80", size=80)


class DealerAssign(models.TransientModel):

    """
    Dealer Assign wizard.

    Loaded to assign a sales person to multiple dealers
    """

    _name = 'xpr_dealer.dealer_assign'

    def _init_dealers(self):

        context = self.env.context

        active_ids = context.get('active_ids')

        if not active_ids:
            return []

        return self.env['xpr_dealer.dealer'].browse(active_ids)

    dealers = fields.Many2many(
        'xpr_dealer.dealer',
        'dealer_assign_dealers_rel',
        string='Dealers',
        required=True,
        default=_init_dealers)

    salesperson = fields.Many2one(
        'res.users',
        string='Salesperson',
        required=True)

    @api.multi
    def assign(self):

        for dealer in self.dealers:
            dealer.user_id = self.salesperson
