# -*- coding: utf-8 -*-

{
    'name': 'Xprima Product',
    'version': '0.3',
    'summary': 'Xprima Product',
    'description': """
Adapts product to Xprimas needs.
Adds custom fields and removes unwanted fields from views.
This was originally the xprima_product module for OpenERP.

Features:

- Products may be marked as payable only one time

- Xprima product category definitions

    """,
    'category': 'misc',
    'author': 'Xprima',
    'website': 'www.xprima.com',
    'depends': [
        'product',
        'sale',
        #'contract_isp',
    ],
    'data': [
        'product_view.xml',
        'product_categories.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
