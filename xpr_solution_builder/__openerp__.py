# -*- coding: utf-8 -*-
{
    'name': "Xprima Solution Builder",

    'summary': """
        Add on to package products into one entity
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Xprima Corp",
    'website': "http://www.auto123.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master
    #   /openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/solution_builder.xml',
        'wizard/solution_configurator.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],

}
