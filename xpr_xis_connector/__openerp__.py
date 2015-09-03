# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'XIS Connector',
    'version': '0.3',
    'author': 'Xprima',
    'maintainer': 'Xprima',
    'website': 'http://www.xprima.com',
    'license': 'AGPL-3',
    'category': 'Sale',
    'summary': 'Sync information to XIS',
    'description': """
XIS Connector
=============

Send information to system XIS when create/update field.

The XIS update is to be deprecated eventually.

Functionalities not related to XIS are to be migrated out of it.

Contributors
------------
* Mathieu Benoit <mathieu.benoit@savoirfairelinux.com>
* Charles De Lean <cdelean@xprima.com>
""",
    'depends': [
        'base',
        'crm',
        'sale',
        'hr',
        'xpr_dealer_group',
        'xpr_dropdowns_values',
        'xpr_product',

        #'account',
        #'salesforce_data_mapping',
        #'partner_category_description',
        #'sale_package_configurator',
        #'contract_isp',
        #'account_anglo_saxon',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        #'res.groups.csv',
        'load_french.xml',
        'views/product.xml',
        'views/res_partner.xml',
        'views/res_user.xml',
        #'ir.config_parameter.csv',
        'views/sale.xml',
        #'ir.ui.menu.csv',
        #'security/ir.model.access.csv',
        #'ir.actions.act_window.csv',
        #'product.pricelist.csv',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
