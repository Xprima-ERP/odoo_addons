#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used as a mapping table for partner to partner_business_type.
"""

from openerp.osv import osv, fields


class PartnerPartnerBusinessTypeRel(osv.Model):

    """
    Model used as a mapping table for partner to partner_business_type.
    """
    _name = "partner_partner_business_type_rel"
    _pbti = "partner_business_type_id"
    _columns = {"partner_id": fields.integer("partner_id"),
                _pbti: fields.integer(_pbti), }

PartnerPartnerBusinessTypeRel()
