#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used as a mapping table for partner to partner_portalmask.
"""

from openerp.osv import osv, fields


class PartnerPartnerPortalmaskRel(osv.Model):

    """
    Model used for the selection of a partner_portalmask.
    """
    _name = "partner_partner_portalmask_rel"
    _ppi = "partner_portalmask_id"
    _columns = {"partner_id": fields.integer("partner_id"),
                _ppi: fields.integer(_ppi), }

PartnerPartnerPortalmaskRel()
