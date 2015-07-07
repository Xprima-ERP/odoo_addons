#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used as a mapping table for partner to partner_make_snowmobile.
"""

from openerp.osv import osv, fields


class PartnerPartnerMakeSnowmobileRel(osv.Model):

    """
    Model used for the selection of a partner_make_snowmobile.
    """
    _name = "partner_partner_make_snowmobile_rel"
    _pmsi = "partner_make_snowmobile_id"
    _columns = {"partner_id": fields.integer("partner_id"),
                _pmsi: fields.integer(_pmsi), }

PartnerPartnerMakeSnowmobileRel()
