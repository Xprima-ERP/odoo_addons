#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner portalmask.

Values from Salesforce:
    Auto123 Network
    AMMQ / AQVL
    GM Optimum - Enabled Sites
    Hyundai CPO
    MUCDA Portal
"""

from openerp.osv import osv, fields


class PartnerPortalmask(osv.Model):

    """
    Model used for the selection of a partner portalmask.
    """
    _name = "partner_portalmask"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerPortalmask()
