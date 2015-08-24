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

Note: Install the Sales and Management (sales) module manually first
because of wizard.

Config sets Sales Order id format (C prefix). Sales orders are contracts.
""",

    'category': 'Misc',
    'author': 'Xprima',
    'website': 'http://xprima.com',
    'license': 'AGPL-3',
    'depends': [
        'sale',  # Install manually because of wizard setup
        'hr',
        'crm',
        'agaplan_terms_and_conditions',  # Xprima port for Odoo
        'partner_history',  # Xprima port for Odoo
        'xpr_product',
        'xpr_solution_builder',
        'xpr_sale_process',
        'xpr_product_variant_filters',  # Deprecated ?
        'xpr_report',
        'xpr_dealer_group',
        #'xpr_dropdowns_values',
        #'xpr_xis_connector', # Will be dropped. No rush to port.
        #'xpr_csi_program',
        #'xpr_dealer_group,
        #'xpr_dropdowns_values',

        # From 7.0 version

        # 'project', # Abandoned, was for helpdesk.
        # 'xpr_hd_ticket', # Helpdesk abandoned bridge.

        # 'purchase', # Not useful. Drop it.
        # 'canadian_provinces', # Depecrated. Not using provinces anymore.

        # 'product_custom_attributes', # Replaced by xpr_solution_builder
        # 'web_adblock',
        # 'mass_editing',
        # 'audittrail',

        #'xprima_sale_order',

        #'sale_package_configurator',
        #'so_second_level_approval_and_discount',

        # 'csv_noupdate',
        # 'no_customer_auto_follow',
        # 'xpr_seo',
        # 'xpr_casa',
        # 'hr_employee_auto_create',
        # 'reps_nocreate_dealer',
    ],

    'data': [
        'config.xml'
    ],
    'demo': [],
    'installable': True,
    # 'auto_install': True,
    # 'application': False,
}
