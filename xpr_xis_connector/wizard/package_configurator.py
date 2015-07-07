# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
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

from openerp.osv import orm


class package_configurator(orm.TransientModel):
    """Package Configurator wizard for XIS connector"""

    _inherit = 'contract.service.configurator'

    def do_done(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        status = super(package_configurator, self).do_done(cr, uid, ids,
                                                           context=context)
        # force to do a write in sale_order
        sale_order_obj = self.pool.get('sale.order')
        sale_order_obj.write(cr,
                             uid,
                             [wizard.order_id.id],
                             {},
                             context=context)

        return status
