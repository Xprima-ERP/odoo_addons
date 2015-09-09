#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner make snowmobile.

Values from Salesforce:
    Artic Cat
    Polaris
    Ski-Doo
    Snow-Hawk
    Yamaha
"""

from openerp.osv import osv, fields


class PartnerMakeSnowmobile(osv.Model):

    """
    Model used for the selection of a partner make snowmobile.
    """
    _name = "partner_make_snowmobile"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerMakeSnowmobile()
