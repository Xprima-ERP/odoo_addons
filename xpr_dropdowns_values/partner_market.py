#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a Partner market.

Values from Salesforce:
 calgary
 edmonton
 gta
 montreal
 osprey
 ottawa
 regina
 saskatoon
 vancouver
 victoria
 windsor
 winnipeg
 nanaimo
"""

from openerp.osv import osv, fields


class PartnerMarket(osv.Model):

    """
    Model used for the selection of a Partner market.
    """
    _name = "partner_market"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerMarket()
