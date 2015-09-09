#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a Partner Business Relationship.
"""

from openerp.osv import osv, fields


class PartnerBusinessRelationship(osv.Model):

    """
    Model used for the selection of a Partner Business Relationship.
    """
    _name = "partner_business_relationship"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerBusinessRelationship()
