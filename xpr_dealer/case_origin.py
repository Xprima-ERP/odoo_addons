#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a case origin.

Values from Salesforce:
    Email
    Fax
    Internal
    Phone
    Web
"""

from openerp.osv import osv, fields


class CaseOrigin(osv.Model):

    """
    Model used for the selection of a partner telephone choice.
    """
    _name = "case_origin"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

CaseOrigin()
