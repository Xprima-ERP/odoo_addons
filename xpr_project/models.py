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
        self.create_project()
        super(SaleOrder, self).approve_contract()

    @api.one
    def create_project(self):

        order = self

        if order.project_id:
            return

        routes = self.env['xpr_project.routing'].search([('categories', 'in', [order.category.id])])

        if not routes:
            # No route.
            # order.state = 'sent'
            return

        project = self.env['project.project'].create(dict(
            name="{0} - {1}".format(order.partner_id.name, order.name),
            partner_id=order.partner_id.id
        ))

        order.project_id = project.analytic_account_id

        for route in routes:

            contract = self.env['project.project'].create(dict(
                name="{0} - {1} - {2}".format(
                    order.partner_id.name, order.name, order.category.name),
                partner_id=order.partner_id.id,
                user_id=route.manager.id,
                parent_id=order.project_id.id,
            ))

            order.env['project.task'].create(dict(
                name=order.category.name,
                description=contract.name,
                notes=order.note,
                project_id=contract.id,
                jira_project_name=route.jira_project_name
            ))

    def sale_specifications(self, cr, uid, ids, context):

        ids = [order.project_id for order in self.pool.get('sale.order')]
        projects_ids = project.search(cr, uid, [('analytic_account_id', 'in', ids)])
        return project.attachment_tree_view(cr, uid, projects_ids, context)


class Routing(models.Model):

    _name = "xpr_project.routing"
    jira_project_name = fields.Char(string="JIRA Project")
    manager = fields.Many2one('res.users', string="Project Manager")
    categories = fields.Many2many(
        'product.category', 'xpr_project_routing_category',
        string="Categories")


class task(models.Model):
    _inherit = "project.task"

    @api.depends('stage_id')
    def _start_project(self):
        for task in self:
            if task.stage_id != self.env.ref('project.project_tt_development'):
                continue

            if task.jira_issue_key:
                continue

            task.jira_issue_key = jira_request.CreateIssue(task).execute()

    jira_project_name = fields.Char(string="JIRA Project")
    jira_issue_key = fields.Char(string="JIRA Issue", compute=_start_project)
