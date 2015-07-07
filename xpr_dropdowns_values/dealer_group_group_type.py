#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a Dealer Group groupe type.
"""

from openerp.osv import osv, fields


class DealerGroupGroupType(osv.Model):

    """
    Model used for the selection of a group type .
    """
    _name = "dealer_group_group_type"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

DealerGroupGroupType()
