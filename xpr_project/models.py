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
            # Already created.
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

        order.env['project.task'].create(dict(
            name="Confirm specs",
            description="Specifications must be confirmed to start production",
            project_id=project.id,
            rule='specs'
        ))

        order.project_id = project.analytic_account_id

        for route in routes:

            contract = self.env['project.project'].create(dict(
                name="{0} - {1} - {2}".format(
                    order.partner_id.name, order.name, order.category.name),
                partner_id=order.partner_id.id,
                user_id=route.manager.id,
                parent_id=order.project_id.id,
                state='pending',
            ))

            order.env['project.task'].create(dict(
                name=order.category.name,
                description=contract.name,
                notes=order.note,
                project_id=contract.id,
                jira_project_name=route.jira_project_name,
                active=False,
            ))

    def sale_specifications(self, cr, uid, ids, context):

        project = self.pool.get('project.project')

        ids = [
            order.project_id.id for order in
            self.pool.get('sale.order').browse(cr, uid, ids, context=context)
        ]

        projects_ids = project.search(cr, uid, [('analytic_account_id', 'in', ids)])
        return project.attachment_tree_view(cr, uid, projects_ids, context)


class Routing(models.Model):

    _name = "xpr_project.routing"
    jira_project_name = fields.Char(string="JIRA Project")
    manager = fields.Many2one('res.users', string="Project Manager")
    categories = fields.Many2many(
        'product.category', 'xpr_project_routing_category',
        string="Categories")


class Task(models.Model):
    _inherit = "project.task"

    def sale_specifications(self, cr, uid, ids, context):

        project = self.pool.get('project.project')

        ids = [
            task.project_id.id for task in
            self.browse(cr, uid, ids, context=context)]

        return project.attachment_tree_view(cr, uid, ids, context)

    @api.multi
    def start_project(self):
        """
        Triggers stuff when stage is updated
        """

        for task in self:

            if task.rule == 'specs':
                if task.stage_id != self.env.ref('project.project_tt_deployment'):
                    continue

                # Enable sub projects
                task.project_id.reset_project()

                # Mark order as complete
                for order in self.env['sale.order'].search(
                    [('project_id', '=', task.project_id.analytic_account_id.id)]
                ):
                    order.state = 'sent'

            if task.rule == 'jira':
                if task.stage_id != self.env.ref('project.project_tt_development'):
                    continue

                if not task.jira_issue_key:
                    task.jira_issue_key = jira_request.CreateIssue(task).execute()

    @api.multi
    def ask_update(self):
        """
        Starts Wizard to get specs from rep
        """
        for task in self:
            return {
                'name': 'Specification request',
                'type': 'ir.actions.act_window',
                'res_model': 'xpr_project.update_message',
                'views': [[False, "form"]],
                'target': 'new',
                'view_id': self.env.ref('xpr_project.ask_update_message').id,
                'context': {'project_id': task.project_id.id}
            }

    @api.model
    def read_jira_updates(self):
        tasks = self.search([('stage_id', '=', self.env.ref('project.project_tt_development').id)])

        key_to_tasks = dict([(t.jira_issue_key, t) for t in tasks if t.jira_issue_key])

        updates = jira_request.BrowseTasks(self, key_to_tasks.keys()).execute() or []

        for update in updates:

            target = key_to_tasks[update.jira_issue_key]

        if update.stage_id != target.stage_id:
            target.write({'stage_id': update.stage_id.id})

    @api.multi
    def write(self, vals):

        res = super(Task, self).write(vals)

        if 'stage_id' in vals:
            # Not using a depends. Side order depends on actual value.
            self.start_project()

        return res

    rule = fields.Char(string="Rule", default="jira")
    jira_project_name = fields.Char(string="JIRA Project")
    jira_issue_key = fields.Char(string="JIRA Issue", store=True)


class AskUpdateMessage(models.TransientModel):

    _name = 'xpr_project.update_message'

    def _default_project(self):
        return self.env['project.project'].browse(self._context.get('project_id'))

    @api.one
    def ask_update(self):

        project = self.project_id

        template = self.env.ref('xpr_project.ask_update_mail')

        # Only one project per order
        order = self.env['sale.order'].search([
            ('project_id', '=', project.analytic_account_id.id)
        ])[0]

        values = self.env['email.template'].with_context(message=self.message).generate_email(
            template.id, order.id)

        destination_ids = [order.user_id.partner_id.id]

        values['recipient_ids'] = [(4, pid) for pid in destination_ids]

        self.env['mail.mail'].create(values)

    project_id = fields.Many2one('project.project', default=_default_project)
    message = fields.Text("Message")
