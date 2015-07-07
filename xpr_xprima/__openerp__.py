# -*- coding: utf-8 -*-
{'name': 'Xprima Modules',
 'version': '1.0',
 'summary': 'Xprima Module Dependencies',
 'description': """Contains all the Xprima dependencies
      Including its own cosum modules:
      - Sales process
      - Reports
 """,
 'category': 'Misc',
 'author': 'Charles De Lean',
 'website': 'http://xprima.com',
 'license': 'AGPL-3',
 'depends': [
      'sale', # Install manually because of wizard setup
      'hr',
      'crm',
      'xpr_solution_builder',
      'xpr_sale_process',
      'xpr_product_variant_filters',
      'agaplan_terms_and_conditions',
      'xpr_report',
      'xpr_xis_connector',
      'xpr_csi_program',

      # From 7.0 version

      # 'project',
      # 'purchase',
      # 'canadian_provinces',

      # 'partner_history',
      # 'product_custom_attributes',
      # 'web_adblock',
      # 'mass_editing',
      # 'audittrail',
      # 'xprima_product',
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
