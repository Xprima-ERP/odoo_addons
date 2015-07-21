#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner make watercraft.

Values from Salesforce:
    Honda
    Kawasaki
    Sea-Doo
    Yamaha
"""

from openerp.osv import osv, fields


class PartnerMakeWatercraft(osv.Model):

    """
    Model used for the selection of a partner make watercraft.
    """
    _name = "partner_make_watercraft"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerMakeWatercraft()
