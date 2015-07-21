#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner categorization field.

Values from Salesforce:
    Duplicate Account
    Not in Master File (Update Date within one Year)
    Closed
    Not in Master File (Update Date Greater than 1 Year)
"""

from openerp.osv import osv, fields


class PartnerCategorizationField(osv.Model):

    """
    Model used for the selection of a partner categorization field.
    """
    _name = "partner_categorization_field"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerCategorizationField()
