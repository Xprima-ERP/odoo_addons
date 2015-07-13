# -*- coding: utf-8 -*-
{'name': 'Xprima Setup Module',
 'version': '1.0',
 'summary': 'Installs all Xprimas modules and dependencies',
 'description': """
Contains all the Xprima dependencies.
Meant to build a db from scratch.
Including its own custom modules:
* Sales process
* Reports
* Worflow

Note: Install the Sales and Management (sales) module manually first beause of wizard.

 """,
 'category': 'Misc',
 'author': 'Charles De Lean',
 'website': 'http://xprima.com',
 'license': 'AGPL-3',
 'depends': [
      'sale', # Install manually because of wizard setup
      'hr',
      'crm',
      'xpr_product',
      'xpr_solution_builder',
      'xpr_sale_process',
      'xpr_product_variant_filters',
      'agaplan_terms_and_conditions',
      'xpr_report',
      #'xpr_dealer_group,
      #'xpr_dropdowns_values',
      #'xpr_xis_connector',
      #'xpr_csi_program',
      #'xpr_dealer_group,
      #'xpr_dropdowns_values',


      # From 7.0 version

      # 'project',
      # 'purchase',
      # 'canadian_provinces',

      # 'partner_history',
      # 'product_custom_attributes',
      # 'web_adblock',
      # 'mass_editing',
      # 'audittrail',
      
      #'xprima_sale_order',

      #'sale_package_configurator',
      #'so_second_level_approval_and_discount',

      # 'csv_noupdate',
      # 'xpr_hd_ticket',
      # 'no_customer_auto_follow',
      # 'xpr_seo',
     
      # 'xpr_casa',
      # 'hr_employee_auto_create',
      # 'reps_nocreate_dealer',
            ],
 'data': [],
 'demo': [],
 'installable': True,
 # 'auto_install': True,
 # 'application': False,
}
