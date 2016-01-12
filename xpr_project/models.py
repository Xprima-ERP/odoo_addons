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

    def approve_contract(self):
        """
        Extends approval action. Called in workflow.
        """

        # If fails, do not execute super
        self._create_contract()
        super(SaleOrder, self).approve_contract()

    def _create_contract(self):

        project_categories = [
            self.env.ref("xpr_product.{0}".format(name))
            for name in ['website']
        ]

        if self.category not in project_categories:
            return None

        contract = self.env['project.project'].create(dict(
            name="{0} - {1}".format(self.partner_id.name, self.name),
            order=self.id
        ))


class Project(models.Model):
    _inherit = "project.project"

    order = fields.Many2one('sale.order', string="Original Order")

    @api.one
    def start_project(self):
        jira_request.LinkProject(self).execute()
