#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used as a mapping table for partner to partner_make_moto.
"""

from openerp.osv import osv, fields


class PartnerPartnerMakeMotoRel(osv.Model):

    """
    Model used for the selection of a partner_make_moto.
    """
    _name = "partner_partner_make_moto_rel"
    _pmmi = "partner_make_moto_id"
    _columns = {"partner_id": fields.integer("partner_id"),
                _pmmi: fields.integer(_pmmi), }

PartnerPartnerMakeMotoRel()
