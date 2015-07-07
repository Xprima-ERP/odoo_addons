#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner make atv.

Values from Salesforce:
    Arctic Cat
    Bombardier
    Bombardier (BRP)
    Can-Am
    E-Ton
    Gas Gas
    Honda
    Kawasaki
    Nordic Motor
    PGO
    Polaris
    Suzuki
    Yamaha
"""

from openerp.osv import osv, fields


class PartnerMakeATV(osv.Model):

    """
    Model used for the selection of a partner make atv.
    """
    _name = "partner_make_atv"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerMakeATV()
