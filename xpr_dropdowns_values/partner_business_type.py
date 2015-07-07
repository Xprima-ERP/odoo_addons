#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a Partner business type.

choices are:
 en
  New Car
  Used Car
  New Moto
  Used Moto
  New ATV
  Used ATV
  New Snowmobile
  Used Snowmobile
  New Watercraft
  Used Watercraft
 fr
  Nouvelle voiture
  Voiture usagée
  Nouvelle moto
  Moto usagée
  Nouveau VTT
  VTT usagé
  Nouvelle motoneige
  Motoneige usagée
  Nouveau Véhicule marin
  Véhicule marin usagé
"""

from openerp.osv import osv, fields


class PartnerBusinessType(osv.Model):

    """
    Model used for the selection of a Partner business type.
    """
    _name = "partner_business_type"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerBusinessType()
