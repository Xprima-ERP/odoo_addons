# -*- coding: utf-8 -*-
{
    'name': "Xprima Solution Builder",

    'summary': """
        Add on to package products into a solution
        """,

    'description': """
        Products are packaged together in order to simplify quotations in the Xprimas workflow.
        
        This module:

        - Permits building solutions

        - Attaches a solution to a sales order (quotation/contract)

        - Replaces sales line population in sales order whenever a solution is selected.
        
    """,

    'author': "Xprima Corp",
    'website': "http://www.xprima.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp
    # /addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'views/solution_builder.xml',
        'views/solution_configurator.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],

}
