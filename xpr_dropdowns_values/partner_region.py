#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Model used for the selection of a Partner region.

Values from Salesforce:
    Medicine Hat (div#1)
    Lethbridge (div#2)
    Fort Macleod (div#3)
    Hanna (div#4)
    Drumheller (div#5)
    Calgary (div#6)
    Stettler (div#7)
    Red Deer (div#8)
    Rocky Mountain House (div#9)
    Camrose-Lloydminster (div#10)
    Edmonton (div#11)
    St. Paul (div#12)
    Athabasca (div#13)
    Edson (div#14)
    Banff (div#15)
    Fort McMurray (div#16)
    Slave Lake (div #17)
    Grande Cache (div#18)
    Grande Prairie (div#19)
    Barrie
    Hamilton
    Kenora
    Kingston
    Kitchener/Waterloo
    London
    Manitoulin Island
    Moose Factory
    Niagara Falls
    North Bay
    Ottawa
    Owen Sound
    Sudbury
    Sarnia
    Sault Ste. Marie
    Thunder Bay
    Timmins
    Toronto
    Windsor
    Abitibi/Témiscamingue
    Bois-Francs
    Bas-Saint-Laurent
    Chaudière-Appalaches
    Côte-Nord
    Estrie
    Gaspésie/Iles de la Madeleine
    Laurentides
    Lanaudière
    Laval
    Mauricie
    Montérégie
    Montréal
    Nord-du-Québec
    Outaouais
    Québec
    Saguenay/Lac-St-Jean
"""

from openerp.osv import osv, fields


class PartnerRegion(osv.Model):
    """
    Model used for the selection of a Partner region.
    """
    _name = "partner_region"
    _columns = {"name": fields.char("Name",
                                    size=64,
                                    required=True,
                                    translate=True),
                'code': fields.char('Code',
                                    size=2,
                                    required=True), }

PartnerRegion()
