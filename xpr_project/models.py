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
import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def approve_contract(self):
        """
        Extends approval action. Called in workflow.
        """

        # If fails, do not execute super
        self.create_project()
        super(SaleOrder, self).approve_contract()

    @api.depends('live_date', 'order_line')
    def _get_renew_date(self):
        for order in self:

            date = order.live_date

            if date:
                date = fields.Date.from_string(date)
            else:
                continue

            if order.category.id == self.env.ref('xpr_product.website').id:
                delta = datetime.timedelta(days=365 * 2)
            else:
                months = [
                    line.product_uom_qty for line in order.order_line
                    if line.product_id.id and not line.product_id.one_time_payment
                ]

                if months:
                    delta = datetime.timedelta(days=31 * max(months))
                else:
                    # Not supposed to get here. Default to 2 years.
                    delta = datetime.timedelta(days=365 * 2)

            date = fields.Date.to_string(date + delta)

            order.renew_date = date

    def _route_account_manager(self):
        """
        Calculates account manager when routing order/order signed
        """
        class RouteContext(object):
            def __init__(self, order):
                self.order = order

            @property
            def state(self):
                return self.order.partner_id.state_id.code

        routes = self.env['xpr_project.account_manager'].search([])

        ctx = RouteContext(self)

        context = {'ctx': ctx}

        for route in routes:
            if not route.rule:
                continue

            try:
                if not eval(route.rule, context):
                    continue

                return route.manager
            except Exception as e:
                # TODO: Log error?
                pass

        return None

    def _expected_delivery(self, today):
        """
        Calculates expected delivery date when routing order/order signed
        """

        today = fields.Date.from_string(today)
        delivery_date = today

        if self.live_date:
            delivery_date = fields.Date.from_string(self.live_date)
        else:
            # Might have some filters one day. For now, simply return first found.

            for delay in self.env['xpr_project.delivery_delay'].search([]):
                delivery_date = today + datetime.timedelta(days=delay.delay)
                break

        # Whatever was found, be sure it is not in the past.
        return fields.Date.to_string(max(delivery_date, today))

    @api.one
    def create_project(self):

        order = self

        if order.project_id:
            # Already created.
            return

        if not order.category:
            # Cannot route. Probably legacy order
            return

        routes = self.env['xpr_project.routing'].search([('categories', 'in', [order.category.id])])

        if not routes:
            # No route.
            # order.state = 'sent'
            return

        # Create project

        manager = order._route_account_manager()

        today = fields.Date.context_today(self)

        # Calculate expected delivery date
        order.expected_delivery_date = order._expected_delivery(today)

        project = self.env['project.project'].create(dict(
            name=u"{0} - {1}".format(order.partner_id.name, order.name),
            partner_id=order.partner_id.id,
            user_id=manager and manager.id or None,
            date_start=today,
            date=order.expected_delivery_date,
            salesperson=order.user_id.id,
            state='draft'
        ))

        order.env['project.task'].create(dict(
            name="Confirm specs",
            description="Specifications must be confirmed to start production",
            project_id=project.id,
            rule='specs',
            salesperson=order.user_id.id,
            date_start=today,
            date_end=project.date,
        ))

        # Add empty attachment for all subprojets

        names = set([
            label.name
            for label in order.env['xpr_project.attachment.label'].search([])
        ])

        for name in names:
            order.env['ir.attachment'].create(dict(
                res_model='project.project',
                res_id=project.id,
                name=name))

        # Link project to order

        order.project_id = project.analytic_account_id

        # Send mail to affected project managers

        template = self.env.ref('xpr_project.template_project_confirmation')

        values = self.env['email.template'].generate_email(
            template.id, project.id)

        values['recipient_ids'] = [(4, route.manager.partner_id.id) for route in routes]
        values['recipient_ids'].append((4, order.user_id.partner_id.id))

        self.env['mail.mail'].create(values)

    def sale_specifications(self, cr, uid, ids, context):

        project = self.pool.get('project.project')

        ids = [
            order.project_id.id for order in
            self.pool.get('sale.order').browse(cr, uid, ids, context=context)
        ]

        projects_ids = project.search(cr, uid, [('analytic_account_id', 'in', ids)])
        return project.attachment_tree_view(cr, uid, projects_ids, context)

    expected_delivery_date = fields.Date(
        'Expected Delivery Date',
        help="Estimated delivery date of the project.")

    delivery_date = fields.Date(
        'Delivery Date',
        help="Actual delivery date of the project.")

    live_date = fields.Date(
        'Live Date',
        help="Official launch date of the project.")

    cancel_date = fields.Date(
        'Cancel Date',
        help="Signed contract was cancelled at this date.")

    renew_date = fields.Date(
        'Renew Date', compute=_get_renew_date, store=True,
        help="Date of contract renewal.")


class Attachment(models.Model):

    _inherit = 'ir.attachment'

    @api.one
    def file_open(self):
        """
        Copied from _file_read in super class
        Returns a file handle instead of the data
        """
        full_path = self._full_path(self.store_fname)

        try:
            return open(full_path, 'rb')
        except IOError:
            return None


class AttachmentLabel(models.Model):
    """
    Tags reserved to name attachments.
    """

    _name = "xpr_project.attachment.label"
    _inherit = "project.category"


class Routing(models.Model):

    _name = "xpr_project.routing"

    jira_template_name = fields.Char(string="JIRA Template Name")
    manager = fields.Many2one('res.users', string="Project Manager")
    categories = fields.Many2many(
        'product.category', 'xpr_project_routing_category',
        string="Categories")

    attachment_names = fields.Many2many(
        'xpr_project.attachment.label', 'xpr_project_routing_attachment',
        string="Attachments")

    _sql_constraints = [
        (
            'uniq_jira_template_name',
            'unique(jira_template_name)',
            "A route already exists with this JIRA template. Key must be unique."
        ),
    ]


class AccountManager(models.Model):
    _name = 'xpr_project.account_manager'
    _order = 'sequence'

    sequence = fields.Integer(string="Sequence")
    rule = fields.Char(string="Rule")
    manager = fields.Many2one('res.users', string="Account Manager", required=True)


class DeliveryDelay(models.Model):
    _name = 'xpr_project.delivery_delay'

    delay = fields.Integer(string="Delay in Days", default=60)


class Project(models.Model):

    _inherit = "project.project"

    @api.one
    def create_sub_tasks(self, order):

        order.state = 'waiting_date'

        routes = self.env['xpr_project.routing'].search([('categories', 'in', [order.category.id])])

        date_start = fields.Date.context_today(self)

        for route in routes:

            vals = dict(
                user_id=route.manager.id,
                name=order.category.name,
                salesperson=order.user_id.id,
                description=order.name,
                notes=order.note,
                project_id=self.id,
                jira_template_name=route.jira_template_name,
                date_start=date_start,
                date_end=self.date,
            )

            order.env['project.task'].create(vals).trigger_project()

        self.state = 'open'

    @api.multi
    def start_project(self):
        """
        Triggers stuff when stage is updated
        """

        for task in self.tasks:

            if task.rule == 'specs':
                task.stage_id = self.env.ref('project.project_tt_deployment')
            else:
                task.stage_id = self.env.ref('project.project_tt_development')

    @api.multi
    def sale_specifications(self):

        for project in self:
            for task in project.tasks:

                if task.rule == 'specs':
                    return task.sale_specifications()

    @api.multi
    def ask_update(self):
        """
        Starts Wizard to get specs from rep
        """
        for project in self:
            for task in project.tasks:

                if task.rule == 'specs':
                    return task.ask_update()

    @api.multi
    def set_live(self):

        date = self.env.context.get("live_date", fields.Date.context_today(self))

        ids = [project.analytic_account_id.id for project in self]

        self.env['sale.order'].search([
            ('project_id', 'in', ids)
        ]).live_date = date

        self.notify_project_live()

    @api.multi
    def notify_project_live(self):

        # Send mail to accounting

        template = self.env.ref('xpr_project.template_order_bill_ready')

        for project in self:

            order = self.env['sale.order'].search([
                ('project_id', '=', project.analytic_account_id.id)
            ])

            values = self.env['email.template'].generate_email(
                template.id, order.id)

            values['recipient_ids'] = [
                (4, u.partner_id.id)
                for u in self.env.ref('account.group_account_user').users
                if u.partner_id
            ]

            self.env['mail.mail'].create(values)

    salesperson = fields.Many2one(
        'res.users',
        string="Salesperson",
        help="Source of contract and provider of specs.")

    specs_approval_date = fields.Date(
        string="Specs Approval Date",
        help="Approval date of the specifications provided to begin the project.",
        readonly=True)

    # Template helper
    @property
    def form_url(self):
        return "/web#id={0}&view_type=form&model=project.project".format(
            self.id)


class Task(models.Model):
    _inherit = "project.task"

    def sale_specifications(self, cr, uid, ids, context):

        project = self.pool.get('project.project')

        ids = [
            task.project_id.id for task in
            self.browse(cr, uid, ids, context=context)]

        return project.attachment_tree_view(cr, uid, ids, context)

    @api.multi
    def trigger_project(self):
        """
        Triggers stuff when stage is updated
        """

        for task in self:

            if task.rule == 'specs':
                if task.stage_id != self.env.ref('project.project_tt_deployment'):
                    continue

                # Mark order as complete
                order = self.env['sale.order'].search([
                    ('project_id', '=', task.project_id.analytic_account_id.id)
                ])

                today = fields.Date.context_today(self)

                order.date_confirm = today
                task.project_id.specs_approval_date = today

                task.project_id.create_sub_tasks(order)

            if task.rule == 'jira':

                if task.stage_id != self.env.ref('project.project_tt_development'):
                    continue

                if task.jira_issue_key:
                    continue

                task.with_context(from_jira=True).write({
                    'jira_issue_key': jira_request.CreateIssue(task).execute()})

                # Mark order as in production
                order = self.env['sale.order'].search([
                    ('project_id', '=', task.project_id.analytic_account_id.id)
                ])

                order.state = 'production'

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
                'context': {
                    'project_id': task.project_id.id,
                    'salesperson': task.salesperson.id
                }
            }

    @api.model
    def read_jira_updates(self):
        # Check tasks in development

        done = self.env.ref('project.project_tt_deployment')
        development = self.env.ref('project.project_tt_development')

        tasks = self.search([
            ('stage_id', '=', development.id),
            ('rule', 'in', ['jira', 'legacy']),
        ])

        key_to_tasks = dict([(t.jira_issue_key, t) for t in tasks if t.jira_issue_key])

        updates = jira_request.BrowseTasks(self, key_to_tasks.keys()).execute() or []

        projects = dict()
        live_tasks = dict()
        cancelled_tasks = dict()

        for update in updates:

            target = key_to_tasks[update.jira_issue_key]

            if update.stage_id == target.stage_id:
                continue

            target.with_context(from_jira=True).write({'stage_id': update.stage_id.id})

            project_key = update.jira_issue_key.split('-')[0]

            if update.live_date:
                live_tasks[target.id] = update.live_date

            if update.cancel_date:
                cancelled_tasks[target.id] = update.cancel_date

            if update.stage_id != development and target.rule == 'jira':
                projects[target.project_id.id] = target.project_id

        for key, project in projects.items():

            order = self.env['sale.order'].search([
                ('project_id', '=', project.analytic_account_id.id)
            ])

            ids = set([t.id for t in project.tasks if t.rule in ['jira', 'legacy']])

            if ids <= set(live_tasks.keys()):
                # All tasks are cancelled
                project.with_context(
                    live_date=max([live_tasks[t] for t in ids])
                ).set_live()

            if ids <= set(cancelled_tasks.keys()):
                # All tasks are cancelled
                order.cancel_date = max([cancelled_tasks[t] for t in ids])

            if [t for t in project.tasks if t.stage_id != done]:
                # Not all done
                continue

            project.set_done()

            # Deactivates tasks in project tree
            # p.set_template()

            # Order goes to next step
            order.state = 'manual'
            order.delivery_date = fields.Date.context_today(order)

    @api.multi
    def _jira_url(self):
        for task in self:

            if not task.jira_issue_key:
                task.jira_url = ''
                continue

            task.jira_url = '{0}/browse/{1}'.format(
                self.env.ref('xpr_project.config_param_url').value,
                self.jira_issue_key
            )

    @api.multi
    def write(self, vals):

        if 'stage_id' in vals and not self.env.context.get('from_jira'):
            # JIRA tasks stage_ids can be set to 'done' or 'cancel' from Jira update only

            has_jira_task = False
            impossible_stage_updates = set()

            for task in self:
                if task.rule == 'jira':
                    has_jira_task = True
                    break

            if has_jira_task:
                impossible_stage_updates = set([
                    self.env.ref('project.project_tt_deployment').id,
                    self.env.ref('project.project_tt_cancel').id,
                ])

            if vals['stage_id'] in impossible_stage_updates:
                # Manual update not possible for this stage.

                del vals['stage_id']

        super(Task, self).write(vals)

        if self.env.context.get('from_jira'):
            # Not user interaction. No need to go further.
            # This avoids recursive loops.

            return

        if 'stage_id' in vals:
            # Not using a 'depends' decorator.
            # Update depends on actual value in db.

            self.trigger_project()

    rule = fields.Char(string="Rule", default="jira")
    jira_template_name = fields.Char(string="JIRA Project Template")
    jira_issue_key = fields.Char(string="JIRA Issue", required=False)
    jira_url = fields.Char(string="JIRA Url", compute=_jira_url)
    salesperson = fields.Many2one('res.users', string="Salesperson")
    specs_approval_date = fields.Date(
        string="Specs Approval Date",
        help="Approval date of the specifications provided to begin the project.",
        readonly=True,
        related="project_id.specs_approval_date")

    _sql_constraints = [
        (
            'uniq_jira_issue_key',
            'unique(jira_issue_key)',
            "A task already exists with this JIRA key. Key must be unique."
        ),
    ]


class AskUpdateMessage(models.TransientModel):

    _name = 'xpr_project.update_message'

    def _default_project(self):
        return self.env['project.project'].browse(self._context.get('project_id'))

    def _default_salesperson(self):
        return self.env['res.users'].browse(self._context.get('salesperson'))

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

        destination_ids = [
            order.user_id.partner_id.id
        ] + [
            u.partner_id.id for u in self.carbon_copy
        ]

        values['recipient_ids'] = [(4, pid) for pid in destination_ids]

        self.env['mail.mail'].create(values)

    project_id = fields.Many2one('project.project', default=_default_project)
    salesperson = fields.Many2one('res.users', string="Salesperson", default=_default_salesperson)
    message = fields.Text("Message")
    carbon_copy = fields.Many2many('res.users', string="Also to:")
