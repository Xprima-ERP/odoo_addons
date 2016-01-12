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

_logger = logging.getLogger(__name__)

CONFIG_KEY_ENABLE = 'jira.enable'
CONFIG_KEY_URL = 'jira.url'
CONFIG_KEY_PRODUCTION_PROJECT = 'jira.production.project'
CONFIG_KEY_USER = 'jira.config_param_user'
CONFIG_KEY_PWD = 'jira.config_param_pwd'


class JIRARequest(object):

    _jira = None
    _config_params = None

    """
    Class to send request to XIS software. Using POST http request.
    """

    def __init__(self, project):
        self.project = project

    def get_config(self, key):

        if not self._config_params:
            self._config_params = project.env['ir.config_parameter']

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
                return None

            self._jira = JIRA(
                basic_auth=(
                    elf.get_config(CONFIG_KEY_USER),
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
        except Exception as e:
            _logger.error("jira connector error: {0}".format(e))
            raise

    def safe_execute(self):
        """
        Override this method in subclasses to implement
        """
        return None


class CreateIssueRequest(JIRARequest):

    def get_project(self):
        """
        Override this function to provide the JIRA project name
        """

        return None

    def safe_execute(self):

        i = self.jira.create_issue(
            fields=dict(
                project={'key': self.get_project()},
                summary='Remote test',
                description='This is a test',
                issuetype={'name': 'Story'}))

        #jira.add_attachment(i.key, "~/Desktop/deleteme")

        #jira.add_comment(i.key, "My comment")

        # t = self.jira.create_issue(
        #     fields=dict(
        #         project={'key': self.get_project()},
        #         summary='Sub task test',
        #         description='This is a task test',
        #         issuetype={'name': 'Sub-task'},
        #         parent={ 'id' : rootnn.key}))


class CreateProduction(CreateIssueRequest):

    def get_project(self):
        """
        Override this function to provide the JIRA project name
        """

        return self.get_config(CONFIG_KEY_PRODUCTION_PROJECT)
