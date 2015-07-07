#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a customermask.

possible values:
 Auto123
 CCAQ
"""

from openerp.osv import osv, fields


class Customermask(osv.Model):

    """
    Model used for the selection of a customermask.
    """
    _name = "customermask"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

Customermask()
