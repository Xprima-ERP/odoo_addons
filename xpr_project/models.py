# -*- encoding: utf-8 -*-
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


from openerp import models, fields, api
from openerp.tools.translate import _
import jira_request


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Creates project when sales order is approved
    # TODO: Take care of cancellation too. Stop project, propagate to JIRA
    # Called by automated action
    @api.one
    def _trigger_project(self):
        if self.state == 'contract_approved':
            self.env['project.project'].create_from_order(self)


class Project(models.Model):
    _inherit = "project.project"

    @api.model
    def create_from_order(self, order):
        return self.create(dict(
            name="{0} - {1}".format(order.partner_id.name, order.name),
        ))
