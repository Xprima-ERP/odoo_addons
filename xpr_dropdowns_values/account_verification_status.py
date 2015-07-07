#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of an Account Verification Status.
The choices are:
 fr:
  Complet
  En vérification
 en:
  Complete
  Verifying
"""

from openerp.osv import osv, fields


class AccountVerificationStatus(osv.Model):

    """
    Model used for the selection of an Account Verification Status.
    """
    _name = "account_verification_status"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

AccountVerificationStatus()
