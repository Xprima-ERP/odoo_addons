# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2010 - 2014 Savoir-faire Linux
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
    'name': 'Xprima Reports',
    'version': '0.2',
    'author': 'Xprima',
    'maintainer': 'Xprima',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'AGPL-3',
    'category': 'Others',
    'summary': 'Xprimas custom reports',
    'description': """
Client
======
This module contains Xprimas customized report.

Includes Xprimas config of Terms and conditions.

Contributors
------------
* Mathieu Benoit (mathieu.benoit@savoirfairelinux.com) version 7.0
* Charles De Lean (cdelean@xprima.com) port 8.0
""",
    'depends': [
        'sale',
        'xpr_product',
        'xpr_project'
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'sale_order_custom_report.xml',
        'terms_and_conditions.xml',
        'companies.xml',
    ],
    'installable': True,
}
