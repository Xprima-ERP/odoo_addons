#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used as a mapping table for partner to customermask.
"""

from openerp.osv import osv, fields


class PartnerCustomermaskRel(osv.Model):

    """
    Model used for the selection of a customermask.
    """
    _name = "partner_customermask_rel"
    _columns = {"partner_id": fields.integer("partner_id"),
                "customermask_id": fields.integer("customermask_id"), }

PartnerCustomermaskRel()
