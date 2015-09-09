#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a partner make car.

Values from Salesforce:
    Acura
    AMGeneral
    AstonMartin
    Audi
    Bentley
    BMW
    Bugatti
    Buick
    Cadillac
    Campagna
    Chevrolet
    Chrysler
    Daewoo
    Dodge
    Ferrari
    Fiat
    Ford
    FordSVT
    Freightliner
    GMC
    Hino
    Holiday
    Honda
    Hummer
    Hyundai
    Infiniti
    International
    Isuzu
    Jaguar
    Jeep
    Kenworth
    Kia
    Lada
    Lamborghini
    LandRover
    Lexus
    Lincoln
    Lotus
    Mack
    Maserati
    Maybach
    Mazda
    Mercedes
    MINI
    Mitsubishi
    Navistar
    Nissan
    Peterbilt
    Pontiac
    Porsche
    Ram
    Rolls-Royce
    S.S.I.
    Saab
    Saturn
    Scion
    Smart
    Spyker
    Subaru
    Suzuki
    Toyota
    Volkswagen
    Volvo
    WesternStar
"""

from openerp.osv import osv, fields


class PartnerMakeCar(osv.Model):

    """
    Model used for the selection of a partner make car.
    """
    _name = "partner_make_car"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True), }

PartnerMakeCar()
