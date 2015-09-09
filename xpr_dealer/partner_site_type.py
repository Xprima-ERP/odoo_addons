#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner site type.

Values from Salesforce:
    Has Website With Us
    Has a link or portals to their site
    Does not have a website
"""

from openerp.osv import osv, fields


class PartnerSiteType(osv.Model):

    """
    Model used for the selection of a partner site type.
    """
    _name = "partner_site_type"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerSiteType()
