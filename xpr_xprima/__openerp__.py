# -*- coding: utf-8 -*-
{
    'name': 'Xprima Setup Module',
    'version': '1.0',
    'summary': 'Installs Xprimas modules, dependencies and config',
    'description': """
Contains all the Xprima dependencies and config.
Meant to build a db from scratch.
Including its own custom modules:

- Sales process
- Reports
- Workflow
- Solution Builder

Install notes:
    1) Install the Sales and Management (sales) module manually first because of wizard.
    2) In Configuration/Sales:
        a) Remove pricelists (Quotations and Sales Orders / Customer Features)
        b) Add Mulitple Sales Teams (Sales Teams / Manage Sales Teams)
        c) Be sure Delivery orders is unchecked (Quotations and Sales Orders / Warehouse Features)

    3) Uninstall purchase

    5) Upgrade 'sale'. This puts back some stuff removed by purchase.
    6) Uninstall stock. Ignore error.
    7) Upgrade product.
    8) Install this module   
""",

    'category': 'Misc',
    'author': 'Xprima',
    'website': 'http://xprima.com',
    'license': 'AGPL-3',
    'depends': [
        'sale',  # Install manually because of wizard setup
        'hr',
        'crm',
        'auditlog',
        'agaplan_terms_and_conditions',  # Xprima port for Odoo
        'partner_history',  # Xprima port for Odoo
        'canadian_provinces',
        'xpr_product',
        'xpr_solution_builder',
        'xpr_sale_process',

        'xpr_report',
        'xpr_dealer',
        'xpr_xis_connector',
        'xpr_csi_program',

        # From 7.0 version

        # 'xpr_dealer_group', # Merged into xpr_dealer
        # 'xpr_dropdowns_values', # Merged into xpr_dealer
        # 'xpr_product_variant_filters',  # Deprecated
        # 'project', # Abandoned, was for helpdesk.
        # 'xpr_hd_ticket', # Helpdesk abandoned bridge.
        # 'sale_package_configurator', # Replaced by xpr_solution_builder
        # 'product_custom_attributes', # Replaced by xpr_solution_builder
        #' xprima_sale_order', # Merged into xpr_solution_builder
        # 'audittrail', # auditlog seems to suffice.

        # 'web_adblock',
        # 'mass_editing',
        #'so_second_level_approval_and_discount',
        # 'csv_noupdate',
        # 'no_customer_auto_follow',
        # 'xpr_seo',
        # 'xpr_casa',
        # 'hr_employee_auto_create',
        # 'reps_nocreate_dealer',
    ],

    'data': [
        'config.xml',
        'companies.xml',
        'load_french.xml',
        'solution_legacy.xml',
    ],
    'demo': [],
    'installable': True,
    # 'auto_install': True,
    # 'application': False,
}
