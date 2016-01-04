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
    'name': 'Xprima Project',
    'version': '0.1',
    'author': 'Xprima',
    'maintainer': 'Xprima',
    'website': 'http://www.xprima.com',
    'license': 'AGPL-3',
    'category': 'Sale',
    'summary': 'Sync project management with Xprima',
    'description': """
Xprima JIRA Connector
=====================

Adapts project management to Xprimas needs:

- Synchs with JIRA for production needs
- Gives high level project status.

Contributors
------------
* Charles De Lean <cdelean@xprima.com>
""",
    'depends': [
        'base',
        #'project',
    ],
    'external_dependencies': {
        #'python': ['jira'],
    },
    'data': [
        #'config.xml',
        # 'views/res_user.xml',
        # 'views/res_partner_categories.xml',
        # 'res_partners_categories.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
