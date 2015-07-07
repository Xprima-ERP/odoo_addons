#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner telephone choice.

Values from Salesforce:
    Phone
    Toll Free
    Evolio Call Tracking
"""

from openerp.osv import osv, fields


class PartnerTelephoneChoice(osv.Model):

    """
    Model used for the selection of a partner telephone choice.
    """
    _name = "partner_telephone_choice"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerTelephoneChoice()
