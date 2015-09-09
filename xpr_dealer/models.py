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

#from openerp.osv import osv, fields


# Unused class for now
# class res_partner_category_cert(osv.osv):
#     _description = 'Partner Categories Certifications'
#     _name = 'res.partner.category.certification'
#     _columns = {
#         'name': fields.char('Certification Name', required=True, size=64,
#                             translate=True),
#         'description': fields.text('Description', translate=True),
#         'automatic': fields.boolean('Automatic'),
#     }
#     _defaults = {
#         'automatic': False,
#     }


# TODO: Before reanabling this, be sure to explore the following alternative:
# - Make a new 'Certification group' table
# - Reference to it from the partner directly or from a partner category.
#
# This might permit to define some certification templates and share then between partners or groups.

# class res_partner_category(osv.osv):
#     _name = 'res.partner.category'
#     _inherit = "res.partner.category"

#     _columns = {
        # 'certification': fields.many2many(
        #     'res.partner.category.certification',
        #     'res_partner_category_certification_rel',
        #     'category_id',
        #     'certification_id',
        #     'Certification'), # Not used yet

        #'x_sf_id': fields.char('Salesforce ID', size=18, select=True), # Deprecated.
        #'x_salesperson': fields.many2one('res.users','Salesperson'),   # Based on client comments, not used anymore.
        #'x_dealergroup': fields.char('Dealergroup', size=254),         # Duplicate of 'name' field. Deprecated.
        #'x_description_fr': fields.char('Description FR', size=254),   # Deprecated. Import description after changing language
    # }

class res_partner(osv.osv):

    def _convert_ids_to_make_names(self, cr, uid, model_name, ids, context=None):
        '''
        convert a list of ids to a list on make names.
        '''
        partner_make_obj = self.pool.get(model_name)
        makes_names = partner_make_obj.browse(cr,
                                              uid,
                                              ids,
                                              context=context)
        return [make.name for make in makes_names]

    def onchange_makes(self,
                       cr,
                       uid,
                       ids,
                       makes_car,
                       makes_moto,
                       makes_atv,
                       makes_watercraft,
                       makes_snowmobile,
                       context=None):
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
                make_names.extend(self._convert_ids_to_make_names(cr,
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

    _inherit = "res.partner"
    _pbr = "partner_business_relationship"
    _avs = "account_verification_status"
    _avsd = "Account Verification Status"
    _pinh = "This field is used by the helpdesk when a dealer wants to modify"\
            " his infos."
    _ownerh = "This field is there for the synchronization to XIS"
    _ownereh = "This field is there for the synchronization to XIS"
    _ppmsr = "partner_partner_make_snowmobile_rel"
    _ppmwr = "partner_partner_make_watercraft_rel"
    _pcf = "partner_categorization_field"
    _columns = {
        'xis_dc': fields.char('XIS dealer code', size=254),
        'xis_makes': fields.char('XIS Makes', size=254),
        "business_relationship_id": fields.many2one(_pbr,
                                                    "Business Relationship",
                                                    required=False),
        "function": fields.char("Job Position", size=128, translate=True),
        "website": fields.char("Website",
                               size=254,
                               help="Website of Partner or Company"),
        "billing_street": fields.char("Billing Street",
                                      size=128,
                                      required=False),
        "billing_street2": fields.char("Billing Street2",
                                       size=128,
                                       required=False),
        "billing_city": fields.char("Billing City", size=128, required=False),
        "billing_state_id": fields.many2one("res.country.state",
                                            "Billing State"),
        "billing_zip": fields.char("ZIP Billing", size=24, required=False),
        "billing_country_id": fields.many2one("res.country",
                                              "Billing Country"),
        "industry_id": fields.many2one("partner_industry",
                                       "Industry",
                                       selection=_sel_func_industry,
                                       required=False),
        "website_french": fields.char("Website French",
                                      size=254,
                                      help="Website of Partner or Company"),
        "account_verification_status_id": fields.many2one(_avs,
                                                          _avsd),
        "pin": fields.char("PIN", size=16, required=False, help=_pinh),
        "site_online_date": fields.date("Site Online Date"),
        "additional_website": fields.char("Additional Website", size=254),
        "area_code": fields.char("Area Code", size=3),
        "corpname": fields.char("Legal Name", size=128),
        "customermask_ids": fields.many2many("customermask",
                                             "partner_customermask_rel",
                                             "partner_id",
                                             "customermask_id",
                                             "Customer of"),
        "dayspastdue": fields.integer("TTR Access Cut Off"),
        "dpd_override": fields.date("Override Until"),
        "hours_bank": fields.float("Hours Bank", digits=(13, 1)),
        "is_dealer": fields.boolean("Is Dealer"),  # Deprecated
        "is_member": fields.boolean("Is Member"),  # Deprecated
        "membertype": fields.many2many("partner_business_type",
                                       "partner_partner_business_type_rel",
                                       "partner_id",
                                       "partner_business_type_id",
                                       "Business Types"),
        "market": fields.selection(_sel_func_market, "Market"),
        "owner": fields.char("Dealership Owner", size=45, help=_ownerh),
        "owneremail": fields.char("Dealership Owner Email",
                                  size=240,
                                  help=_ownereh),
        "quoteflag": fields.boolean("Send Quotes"),
        "responsible": fields.char("Responsible", size=80),
        "region": fields.selection(_sel_func_region, "Region"),
        "site_type_id": fields.many2one("partner_site_type", "Site Type"),
        "tollfree": fields.char("Toll Free Number", size=64),
        "ttr_access": fields.boolean("TakeTheRoad Access"),
        "user10": fields.char("User10", size=10),
        "user12": fields.char("User12", size=12),
        "user12e": fields.char("User12e", size=12),
        "user40": fields.char("User40", size=40),
        "user40e": fields.char("User40e", size=40),
        "user80": fields.char("User80", size=80),
        "callsource_tollfree": fields.char("Evolio Call Tracking", size=64),
        "geolat": fields.float("GEO Latitude", digits=(6, 6), default=False),
        "geolon": fields.float("GEO Longitude", digits=(6, 6), default=False),
        "makes_atv": fields.many2many("partner_make_atv",
                                      "partner_partner_make_atv_rel",
                                      "partner_id",
                                      "partner_make_atv_id",
                                      "ATV Makes"),
        "makes_snowmobile": fields.many2many("partner_make_snowmobile",
                                             _ppmsr,
                                             "partner_id",
                                             "partner_make_snowmobile_id",
                                             "Snowmobile Makes"),
        "makes_watercraft": fields.many2many("partner_make_watercraft",
                                             _ppmwr,
                                             "partner_id",
                                             "partner_make_watercraft_id",
                                             "Watercraft Makes"),
        "makes_car": fields.many2many("partner_make_car",
                                      "partner_partner_make_car_rel",
                                      "partner_id",
                                      "partner_make_car_id",
                                      "Car Makes"),
        "makes_moto": fields.many2many("partner_make_moto",
                                       "partner_partner_make_moto_rel",
                                       "partner_id",
                                       "partner_make_moto_id",
                                       "Moto Makes"),
        "portalmask": fields.many2many("partner_portalmask",
                                       "partner_partner_portalmask_rel",
                                       "partner_id",
                                       "partner_portalmask_id",
                                       "Used Cars On"),
        "telephone_choice_id": fields.many2one("partner_telephone_choice",
                                               "Phone Choice"),
        "categorization_field_id": fields.many2one(_pcf,
                                                   "Categorization Field"),
        "cbb_free_trial_sept_2013": fields.boolean("CBB Free Trial Sept 2013"),
    }


class res_partner_category(osv.Model):
    _inherit = "res.partner.category"
    _columns = {
        'xis_certification_id': fields.integer('XIS certification id'),
    }

class res_partner_category_cert(osv.osv):
    _inherit = "res.partner.category.certification"
    _columns = {
        'xis_certification_id': fields.integer('XIS certification id'),
    }

# Commented out relation models. These repeat the models created in m2m fields 
# class PartnerCustomermaskRel(osv.Model):

#     """
#     Model used for the selection of a customermask.
#     """
#     _name = "partner_customermask_rel"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 "customermask_id": fields.integer("customermask_id"), }


# class PartnerPartnerBusinessTypeRel(osv.Model):

#     """
#     Model used as a mapping table for partner to partner_business_type.
#     """
#     _name = "partner_partner_business_type_rel"
#     _pbti = "partner_business_type_id"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 _pbti: fields.integer(_pbti), }


# class PartnerPartnerMakeATVRel(osv.Model):

#     """
#     Model used for the selection of a partner_make_atv.
#     """
#     _name = "partner_partner_make_atv_rel"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 "partner_make_atv_id": fields.integer("partner_make_atv_id"), }


# class PartnerPartnerMakeCarRel(osv.Model):

#     """
#     Model used for the selection of a partner_make_car.
#     """
#     _name = "partner_partner_make_car_rel"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 "partner_make_car_id": fields.integer("partner_make_car_id"), }


# class PartnerPartnerMakeMotoRel(osv.Model):

#     """
#     Model used for the selection of a partner_make_moto.
#     """
#     _name = "partner_partner_make_moto_rel"
#     _pmmi = "partner_make_moto_id"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 _pmmi: fields.integer(_pmmi), }


# class PartnerPartnerMakeSnowmobileRel(osv.Model):

#     """
#     Model used for the selection of a partner_make_snowmobile.
#     """
#     _name = "partner_partner_make_snowmobile_rel"
#     _pmsi = "partner_make_snowmobile_id"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 _pmsi: fields.integer(_pmsi), }


# class PartnerPartnerMakeWatercraftRel(osv.Model):

#     """
#     Model used for the selection of a partner_make_watercraft.
#     """
#     _name = "partner_partner_make_watercraft_rel"
#     _pmwi = "partner_make_watercraft_id"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 _pmwi: fields.integer(_pmwi), }


# class PartnerPartnerPortalmaskRel(osv.Model):

#     """
#     Model used for the selection of a partner_portalmask.
#     """
#     _name = "partner_partner_portalmask_rel"
#     _ppi = "partner_portalmask_id"
#     _columns = {"partner_id": fields.integer("partner_id"),
#                 _ppi: fields.integer(_ppi), }
