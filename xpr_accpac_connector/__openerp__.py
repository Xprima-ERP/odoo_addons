# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    'name': 'Xprima ACCPAC Connector',
    'version': '0.1',
    'author': 'Xprima',
    'maintainer': 'Xprima',
    'website': 'http://www.xprima.com',
    'license': 'AGPL-3',
    'category': 'Partner',
    'summary': '',
    'description': """
ACCPAC module
==================
Xprimas ACCPAC connector.

Contributors
------------
* Charles De Lean (cdelean@xprima.com)
""",
    'depends': [
        "base",
        "account",
        "xpr_dealer"
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/partner.xml',
        'views/invoices.xml',
    ],
    'installable': True,
}
