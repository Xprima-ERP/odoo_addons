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
CONFIG_KEY_PRODUCTION_PROJECT = 'jira.production.project'
CONFIG_KEY_USER = 'jira.user'
CONFIG_KEY_PWD = 'jira.pwd'
CONFIG_KEY_SITE_URL = 'web.base.url'


class JIRARequest(object):

    _jira = None
    _config_params = None

    """
    Class to send request to XIS software.
    Using POST http request.
    Instances are seen as decorators around and Odoo models instance
    """

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


class CreateIssue(JIRARequest):

    def safe_execute(self):

        # Instance is a task
        task = self.instance

        order = task.env['sale.order'].search(
            [('project_id', '=', task.project_id.parent_id.id)])

        if not order:
            _logger.info("JIRA update: Order not found for project {0}".format(
                task.project_id.name))

            return None

        # Create Story

        fields = dict(
            project={'key': task.jira_project_name},
            summary=task.project_id.name,
            description='Project for order [{0}|{1}{2}]'.format(
                order.name,
                self.get_config(CONFIG_KEY_SITE_URL),
                order.form_url,
            ),
            issuetype={'name': 'Story'})

        _logger.info("JIRA request {0}".format(fields))

        story = self.jira.create_issue(fields=fields)

         # Copy attachments

        root_project = task.env['project.project'].search([
            ('analytic_account_id', '=', task.project_id.parent_id.id)
        ])[0]

        for attachment in task.env['ir.attachment'].search([
            ('res_model', '=', 'project.project'),
            ('res_id', '=', root_project.id)]
        ):
            stream = io.StringIO(unicode(attachment.datas.decode('base64')))
            self.jira.add_attachment(story.key, stream, filename=attachment.datas_fname)

        # Each order line becomes a task

        for line in order.order_line:

            if not line.product_id:
                # Filter out correction order lines
                continue

            fields = dict(
                project={'key': task.jira_project_name},
                issuetype={'name': 'Technical Task'},
                parent={'id': story.key},
                summary=line.product_id.name or line.product_id.default_code,
                description=line.product_id.description_sale or ''
            )

            print 'Task', fields
            self.jira.create_issue(fields=fields)

        return story and story.key or None
