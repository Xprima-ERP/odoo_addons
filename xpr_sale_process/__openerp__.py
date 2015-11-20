# -*- coding: utf-8 -*-
{
    'name': "Xprima Sale Process",

    'summary': """
    The Xprima Sale Process
    """,

    'description': """
Xprima Sale Process Worflow

Setup:

- Config sets Sales Order id format (C prefix). Sales orders are contracts.
- Quotes can be created directly in views only if user is a manager
- Advertising and All Discounts Sales groups
- Opportunities are solution driven and introduce the notion of funnel score
    """,

    'author': "Xprima",
    'website': "http://www.xprima.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/
    # module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'hr',
        'email_template',
        'xpr_solution_builder',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'ir.ui.menu.csv',
        'sale_workflow.xml',
        'res_groups.xml',
        'crm.case.stage.csv',
        'views/sale_order_view.xml',
        'views/product_category_view.xml',
        'views/opportunity.xml',
        'views/partner.xml',
        'views/message.xml',
        'views/warehouse.xml',
        'opportunity_reminder.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
