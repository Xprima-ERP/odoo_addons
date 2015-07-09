# -*- coding: utf-8 -*-
{
    'name': "Xprima Product Variants Filters",

    'summary': """
    Filters product variants to produce only logical combinations
    """,

    'description': """
       Permits to specify specific attribute combinations when generating product variants.
    """,

    'author': "Xprima",
    'website': "http://www.xprima.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base
    # /module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'product',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'views/filter_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}