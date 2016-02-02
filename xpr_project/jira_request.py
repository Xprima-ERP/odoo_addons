# -*- encoding: utf-8 -*-
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

import logging
import io
import re

_logger = logging.getLogger(__name__)

CONFIG_KEY_ENABLE = 'jira.enable'
CONFIG_KEY_URL = 'jira.url'
CONFIG_KEY_USER = 'jira.user'
CONFIG_KEY_PWD = 'jira.pwd'
CONFIG_KEY_SITE_URL = 'web.base.url'


class JIRARequest(object):

    """
    Base Class to build requests to XIS software.
    Using POST http request.
    Instances are seen as decorators around and Odoo models instance.
    Holds some useful features for all requests:

    - Lazy jira import since jira is not a standard Odoo module
    - Config retrieval
    - Exception handler
    """

    _jira = None
    _config_params = None

    class NoSetup(Exception):
        pass

    def __init__(self, instance):
        self.instance = instance

    def get_config(self, key):

        if not self._config_params:
            self._config_params = self.instance.env['ir.config_parameter']

        lst_param = self._config_params.search([
            ('key', '=', key)])

        if not lst_param:
            return None

        return lst_param[0].value

    @property
    def jira(self):

        if not self._jira:
            # Late import since this library is not standard Odoo.
            # Avoids issues if module is not meant to be installed.

            from jira import JIRA

            enable = (self.get_config(CONFIG_KEY_ENABLE) or '').lower()

            if enable != '1' and enable != 'true':
                _logger.info("jira.enable is not set.")
                raise JIRARequest.NoSetup()

            self._jira = JIRA(
                basic_auth=(
                    self.get_config(CONFIG_KEY_USER),
                    self.get_config(CONFIG_KEY_PWD)),
                server=self.get_config(CONFIG_KEY_URL))

        return self._jira

    def execute(self):
        """
        Main entry point to execute the action
        Manages exceptions
        """
        try:
            return self.safe_execute()
        except JIRARequest.NoSetup:
            return None
        except Exception as e:
            _logger.error("jira connector error: {0}".format(e))
            raise

    def safe_execute(self):
        """
        Override this method in subclasses to implement
        """
        return None


class JIRAParameterContextMapper(object):
    """
    Computes values for different context values available in custom value format strings.
    """
    def __init__(self, order, issue, request):
        self.order = order.with_context(lang='en_US')
        self.partner = self.order.partner_id
        self.dealer = self.partner.dealer
        self.issue = issue
        self.request = request

    @property
    def fields(self):
        return self.issue.fields

    @property
    def dealercode(self):
        return self.partner.code

    @property
    def lang(self):
        lang = self.partner.lang

        if not lang:
            return 'EN'

        return lang.split('_')[0].upper()

    @property
    def new_client(self):
        """
        New client of no order has ever been delivered yet
        """
        orders = self.order.search([
            ('partner_id', '=', self.order.partner_id.id),
            ('delivery_date', '!=', False)])

        return len(orders) and "Yes" or "No"

    @property
    def contract(self):
        return self.order.client_order_ref or ''

    @property
    def province(self):
        return self.partner.state_id.name

    @property
    def account_manager(self):

        if self.partner.state_id.code in ['ON', 'MB', 'AB', 'SK', 'BC']:
            return 'Cliff Denham'

        return 'Dave Bélisle'

    @property
    def package(self):

        # From: VO - New Cars - Starter Express Bilingual
        # Extract: Starter Express

        s = self.order.solution.name.split('-')

        if not s:
            return ""

        s = s[-1].split()

        if len(s) > 2:
            return '{0} {1}'.format(s[0], s[1])
        elif s:
            return s[0]

        return ""

    @property
    def unilingual(self):

        # From: VO - New Cars - Starter Express Unilingual
        # Extract: Unilingual

        s = self.order.solution.name.split('-')

        if not s:
            return ""

        s = s[-1].split()

        if s:
            return s[-1]

        return ""

    @property
    def makes(self):
        return (self.dealer.make_sequence or '').replace(',', ';')

    @property
    def primary_url(self):
        return self.partner.website or ''

    @property
    def date_order(self):
        return self.order.date_order or ''

    @property
    def salesperson(self):
        return self.order.user_id.name

    @property
    def dealer_group(self):
        group_id = self.order.env.ref('xpr_dealer.category_dealer_group').id

        categories = [cat.name for cat in self.dealer.category_id if cat.parent_id.id == group_id]

        if not categories:
            return ''

        return categories[0].title()

    @property
    def order_url(self):
        return "{root}{url}".format(
            root=self.request.get_config(CONFIG_KEY_SITE_URL),
            url=self.order.form_url
        )


class CreateIssue(JIRARequest):

    """
    Class that builds a new Story for a task.

    From order and JIRA template
    - Builds story
    - Adds attachments
    - Adds subtasks
    """

    jira_project_key = None

    # Common formats. Shared custom fields.

    formats = {
        "Account Manager": "{object.account_manager}",
        "Province": "{object.province}",
        #"PTL": "",
        "Package": "{object.package}",
        "Make": "{object.makes}",
        "Dealer Code": "{object.dealercode}",
        "Primary URL": "{object.primary_url}",
        #"Client Status": "Active",
        # "Live Date": "{object.delivery_date}",
        "Contract Date": "{object.date_order}",
        "Representant": "{object.salesperson}",
        "Contract #": "{object.contract}",
        "Dealer Group": "{object.dealer_group}",
        "New Client": "{object.new_client}",
    }

    # Formats reserved for the root projects only
    project_formats = {
        'Default': {
            #'Summary': "{object.dealercode}",
            "Description": u"{object.fields.description}\n*Odoo [{object.order.name}|{object.order_url}]*"
        },
        'EPM': {
            'Summary': "{object.dealercode}",
        },
        'EPMCR': {
            'Summary': u"Inbound Marketing ({object.dealercode})",
        },
    }

    def get_fields(self, context, parent=None):

        issue = context.issue

        field_meta = self.jira.createmeta(
            projectKeys=self.jira_project_key,
            issuetypeNames=issue.fields.issuetype.name,
            expand='projects.issuetypes.fields')['projects'][0]['issuetypes'][0]['fields']

        field_to_format = dict(CreateIssue.formats)

        if parent is None:
            field_to_format.update(CreateIssue.project_formats.get('Default', {}))
            field_to_format.update(
                CreateIssue.project_formats.get(
                    self.jira_project_key, {})
            )

        custom_fields = dict()

        def map_value(name):
            """
            Returns custom field value from context or None
            """

            if name in ['summary', 'description']:

                format_string = field_to_format.get(name.title())

                if not format_string:
                    return None

                return format_string.format(object=context).strip()

            if not name.startswith('customfield'):
                return None

            meta = field_meta[name]

            if meta['name'] not in field_to_format:
                return None

            formatted_value = field_to_format[meta['name']].format(object=context).strip()

            if meta['schema']['type'] == 'date' and formatted_value:
                # Take away possible time part
                formatted_value = formatted_value.split()[0]

            if meta['schema']['custom'].endswith(':select'):
                # Accept only allowed values
                if formatted_value in [val['value'] for val in meta['allowedValues']]:
                    return formatted_value and {'value': formatted_value}

                return None

            elif meta['schema']['custom'].endswith(':multiselect'):
                # Accept only allowed values
                return [
                    {'value': v} for v in formatted_value.split(';')
                    if v in [val['value'] for val in meta['allowedValues']]
                ]
            elif meta['schema']['custom'].endswith(':datepicker'):
                return formatted_value or None

            # Strings/default behavior
            return formatted_value

        # Assignation loop

        for name, value in issue.raw['fields'].items():
            if name not in field_meta:
                continue

            m = map_value(name)

            if not m:
                # No provided value. Default to template.
                m = value

            if m:
                custom_fields[name] = m

        if parent is not None:
            # Sub task case.
            # Insert dealercode in summary if dealercode keyword found.
            # Indicate cloned parent

            summary = issue.fields.summary

            regex = re.compile('dealercode', re.IGNORECASE)

            summary = regex.sub(context.dealercode, summary)

            custom_fields.update(dict(
                parent={'id': parent.key},
                summary=summary,
            ))

        return custom_fields

    def safe_execute(self):

        # Instance is a task
        task = self.instance

        order = task.env['sale.order'].search(
            [('project_id', '=', task.project_id.parent_id.id)])

        if not order:
            _logger.info("JIRA update: Order not found for project {0}".format(
                task.project_id.name))

            return None

        all_tasks = task.search([
            ('project_id.parent_id', 'in', [order.project_id.id])
        ])

        all_routing = task.env['xpr_project.routing'].search([
            ('jira_template_name', 'in', [task.jira_template_name for task in all_tasks])])

        all_attachment_names = set()
        own_attachement_names = set()

        for route in all_routing:
            names = set([label.name for label in route.attachment_names])
            if route.jira_template_name == task.jira_template_name:
                own_attachement_names = names

            all_attachment_names |= names

        self.jira_project_key = task.jira_template_name.split('-')[0]

        template = self.jira.issue(task.jira_template_name)

        project_context = JIRAParameterContextMapper(order, template, self)

        # Create Story

        fields = self.get_fields(project_context)

        _logger.info("JIRA create issue {0}".format(fields))

        story = self.jira.create_issue(fields=fields)

        # Copy non empty attachments

        # Attachement name must be either:
        # - in the routing that created the task
        # - in no other route triggered when subprojects were created.

        root_project = task.env['project.project'].search([
            ('analytic_account_id', '=', task.project_id.parent_id.id)
        ])[0]

        # Refuse attachements used by other routing but not ours.
        refused_attatchments = all_attachment_names - own_attachement_names

        for attachment in task.env['ir.attachment'].search([
            ('res_model', '=', 'project.project'),
            ('res_id', '=', root_project.id),
            ('file_size', '!=', 0)]
        ):
            if attachment.name in refused_attatchments:
                continue

            _logger.info("JIRA add attachment {0}".format(attachment.datas_fname))
            stream = io.StringIO(unicode(attachment.datas.decode('base64')))
            self.jira.add_attachment(story.key, stream, filename=attachment.name)

        # Clone tasks

        lang = project_context.lang

        for task in template.fields().subtasks:
            task = self.jira.issue(task.key)

            summary = task.fields().summary or ''

            if project_context.unilingual == 'Unilingual':
                words = summary.split()

                if ('EN' in words or 'FR' in words) and (lang not in words):
                    # Based on summary, it is language
                    # dependent and current language is not in it
                    continue

            fields = self.get_fields(
                JIRAParameterContextMapper(order, task, self),
                parent=story)

            _logger.info("JIRA create task {0}".format(fields))
            task = self.jira.create_issue(fields=fields)

        return story and story.key or None


class BrowseTasks(JIRARequest):

    """
    Class that reads the statuses of stories related to tasks.

    """

    class TaskModel(object):
        """
        Decorator object that exposes JIRA object as a pseudo task
        """
        def __init__(self, env, instance):
            self.jira_issue_key = instance.key

            status = None

            if instance.fields.resolution:
                status = instance.fields.resolution.name

            if status == 'Completed':
                status = 'project.project_tt_deployment'
            elif not status:
                status = 'project.project_tt_development'
            else:
                status = 'project.project_tt_cancel'

            self.stage_id = env.ref(status)

    def __init__(self, instance, keys):
        super(BrowseTasks, self).__init__(instance)
        self.keys = keys

    def safe_execute(self):
        return [BrowseTasks.TaskModel(self.instance.env, self.jira.issue(key)) for key in self.keys]
