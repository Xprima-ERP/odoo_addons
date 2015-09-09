#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner make moto.

Values from Salesforce:
    American Hotrod
    Aprilia
    Benelli
    BMW
    Buell
    Campagna
    Can-Am
    Chironex
    CMI-Motor
    CPI
    Derbi
    Ducati
    Eton
    Gas Gas
    Harley-Davidson
    Hellbound Steel
    Honda
    Husaberg
    Husqvarna
    Hyosung
    Indian
    Junior
    Kasea
    Kawasaki
    Keeway
    KTM
    Kymco
    LEM
    Nordik Motor
    Moto Guzzi
    OCC
    Pagsta
    Peugeot
    PGO
    Piaggio
    Pitster Pro
    Precision Cycle Works
    Pro-One
    Ridley
    Saxon
    Sherco
    Sym
    Suzuki
    TGB
    TM
    Travertson
    Triumph
    Ural
    Vespa
    Victory
    VOR
    Yamaha
"""

from openerp.osv import osv, fields


class PartnerMakeMoto(osv.Model):

    """
    Model used for the selection of a partner make moto.
    """
    _name = "partner_make_moto"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerMakeMoto()
