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
    def __init__(self, order):
        self.order = order.with_context(lang='en_US')
        self.partner = self.order.partner_id
        self.dealer = self.partner.dealer

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
    def ptl(self):
        return ''

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
        return (self.dealer.make_sequence or '').replace(',',';')

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


class CreateIssue(JIRARequest):

    jira_project_key = None

    """
    Class that builds a new Story for a task.

    From order and JIRA template
    - Builds story
    - Adds attachments
    - Adds subtasks
    """

    def get_custom_fields(self, issue):

        field_meta = self.jira.createmeta(
            projectKeys=self.jira_project_key,
            issuetypeNames=issue.fields.issuetype.name,
            expand='projects.issuetypes.fields')['projects'][0]['issuetypes'][0]['fields']

        # TODO: Move these formats into project config found in database
        field_to_format = {
            #"Account Manager": "", #select
            "Province": "{object.province}",
            "PTL": "{object.ptl}",
            "Package": "{object.package}",
            "Make": "{object.makes}",
            "Dealer Code": "{object.dealercode}",
            "Primary URL": "{object.primary_url}",
            # "Client Status": "", # select
            # "Live Date": "{object.delivery_date}",
            "Contract Date": "{object.date_order}",
            "Representant": "{object.salesperson}",
            "Contract #": "{object.contract}",
            "Dealer Group": "{object.dealer_group}",
            "New Client": "{object.new_client}",
        }

        custom_fields = dict()

        for name, value in issue.raw['fields'].items():
            if not name.startswith('customfield') or name not in field_meta:
                continue

            meta = field_meta[name]

            if meta['name'] in field_to_format:

                formatted_value = field_to_format[meta['name']].format(object=self.context).strip()

                if meta['schema']['type'] == 'date' and formatted_value:
                    # Take away possible time part
                    formatted_value = formatted_value.split()[0]

                if meta['schema']['custom'].endswith(':select'):
                    # Accept only allowed values
                    if formatted_value in [val['value'] for val in meta['allowedValues']]:
                        custom_fields[name] = formatted_value and {'value': formatted_value}
                    else:
                        custom_fields[name] = None
                elif meta['schema']['custom'].endswith(':multiselect'):
                    # Accept only allowed values
                    custom_fields[name] = [
                        {'value': v} for v in formatted_value.split(';')
                        if v in [val['value'] for val in meta['allowedValues']]
                    ]
                elif meta['schema']['custom'].endswith(':datepicker'):
                    custom_fields[name] = formatted_value or None
                else:
                    # Strings
                    custom_fields[name] = formatted_value

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

        self.jira_project_key = task.jira_template_name.split('-')[0]

        template = self.jira.issue(task.jira_template_name)

        self.context = JIRAParameterContextMapper(order)

        # Create Story

        fields = dict(
            project={'key': self.jira_project_key},
            summary=self.context.dealercode,
            description='{description}\n*Odoo [{name}|{root}{url}]*'.format(
                description=template.fields().description,
                name=order.name,
                root=self.get_config(CONFIG_KEY_SITE_URL),
                url=order.form_url,
            ),
            issuetype={'name': template.fields().issuetype.name})

        fields.update(self.get_custom_fields(template))
        _logger.info("JIRA create issue {0}".format(fields))

        story = self.jira.create_issue(fields=fields)

        # Copy non empty attachments

        # Attachement name must be either:
        # - in the routing that created the task
        # TODO: in no route triggered when subprojects were created.

        root_project = task.env['project.project'].search([
            ('analytic_account_id', '=', task.project_id.parent_id.id)
        ])[0]

        for attachment in task.env['ir.attachment'].search([
            ('res_model', '=', 'project.project'),
            ('res_id', '=', root_project.id),
            ('file_size', '!=', 0)]
        ):
            _logger.info("JIRA add attachment {0}".format(attachment.datas_fname))
            stream = io.StringIO(unicode(attachment.datas.decode('base64')))
            self.jira.add_attachment(story.key, stream, filename=attachment.name)

        # Clone tasks

        lang = self.context.lang

        for task in template.fields().subtasks:
            task = self.jira.issue(task.key)

            summary = task.fields().summary or ''

            if self.context.unilingual == 'Unilingual':
                words = summary.split()

                if ('EN' in words or 'FR' in words) and (lang not in words):
                    # Based on summary, it is language
                    # dependent and current language is not in it
                    continue

            fields = dict(
                project={'key': self.jira_project_key},
                issuetype={'name': task.fields().issuetype.name},
                parent={'id': story.key},
                summary=summary.replace(
                    'Dealercode',
                    self.context.dealercode),
                description=task.fields().description or ''
            )

            fields.update(self.get_custom_fields(task))
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

            status = instance.fields.status.name
            if status == 'Resolved':
                status = 'project.project_tt_deployment'
            elif status == 'Closed':
                status = 'project.project_tt_cancel'
            else:
                status = 'project.project_tt_development'

            self.stage_id = env.ref(status)

    def __init__(self, instance, keys):
        super(BrowseTasks, self).__init__(instance)
        self.keys = keys

    def safe_execute(self):
        return [BrowseTasks.TaskModel(self.instance.env, self.jira.issue(key)) for key in self.keys]
