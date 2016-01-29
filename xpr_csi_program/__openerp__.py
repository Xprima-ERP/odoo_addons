# -*- coding: utf-8 -*-

{
    'name': 'Xprima CSI Program',
    'version': '0.1',
    'summary': 'Xprima CSI Program',
    'description': 'Customer Satisfaction Index Program features for Xprima.',
    'category': 'Misc',
    'author': 'Xprima',
    'website': 'http://www.xprima.com',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'sale',
        'xpr_dealer',
        'xpr_solution_builder'
    ],

    'data': [
        'view/sale_order.xml',
        'survey.xml'
    ],

    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
