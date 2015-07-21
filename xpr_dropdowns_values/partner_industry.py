#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a Partner industry.
"""

from openerp.osv import osv, fields


class PartnerIndustry(osv.Model):

    """
    Model used for the selection of a Partner industry.
    """
    _name = "partner_industry"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerIndustry()
