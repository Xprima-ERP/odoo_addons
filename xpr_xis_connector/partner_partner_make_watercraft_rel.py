#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used as a mapping table for partner to partner_make_watercraft.
"""

from openerp.osv import osv, fields


class PartnerPartnerMakeWatercraftRel(osv.Model):

    """
    Model used for the selection of a partner_make_watercraft.
    """
    _name = "partner_partner_make_watercraft_rel"
    _pmwi = "partner_make_watercraft_id"
    _columns = {"partner_id": fields.integer("partner_id"),
                _pmwi: fields.integer(_pmwi), }

PartnerPartnerMakeWatercraftRel()
