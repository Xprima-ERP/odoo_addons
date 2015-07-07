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
    'name': 'Dealer Group',
    'version': '0.2',
    'author': 'Xprima',
    'maintainer': 'Xprima',
    'website': 'http://www.xprima.com',
    'license': 'AGPL-3',
    'category': 'Partner',
    'summary': 'Xprima Dealer Group support',
    'description': """
DealerGroup module
==================
Xprimas Dealer Group support.

Contributors
------------
* Mathieu Benoit (mathieu.benoit@savoirfairelinux.com)
* Charles De Lean (cdelean@xprima.com)
""",
    'depends': [
        #'partner_category_description',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'views/res_partner.xml',
    ],
    'installable': True,
}
