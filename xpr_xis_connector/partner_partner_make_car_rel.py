#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used as a mapping table for partner to partner_make_car.
"""

from openerp.osv import osv, fields


class PartnerPartnerMakeCarRel(osv.Model):

    """
    Model used for the selection of a partner_make_car.
    """
    _name = "partner_partner_make_car_rel"
    _columns = {"partner_id": fields.integer("partner_id"),
                "partner_make_car_id": fields.integer("partner_make_car_id"), }

PartnerPartnerMakeCarRel()
