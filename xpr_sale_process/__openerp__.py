# -*- coding: utf-8 -*-
{
    'name': "Xprima Pre Quote Creation Actions",

    'summary': """
        Add a Pre Quote Creation Actions subactivity to the sale.order.basic
    workflow
    """,

    'description': """
        Add a Pre Quote Creation Actions subactivity to the sale.order.basic
    workflow
    """,

    'author': "Xprima",
    'website': "http://www.xprima.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/
    # module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'sale_workflow.xml',
        'views/sale_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
