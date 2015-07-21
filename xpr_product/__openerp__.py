# -*- coding: utf-8 -*-

{'name': 'Xprima Product',
 'version': '0.2',
 'summary': 'Xprima Product',
 'description': """
 Adds Xprimas product legacy fields and removes unwanted fields from views. 
 This is the port of xprima_product module for OpenERP.
 """,
 'category': 'misc',
 'author': 'Xprima',
 'website': 'www.xprima.com',
 'depends': [
             'product',
             #'contract_isp',
 ],
 'data': [
     'product_view.xml',
 ],
 'installable': True,
 'auto_install': False,
 'application': False,
 }
