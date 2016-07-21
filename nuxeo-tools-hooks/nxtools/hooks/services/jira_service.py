"""
(C) Copyright 2016 Nuxeo SA (http://nuxeo.com/) and contributors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
you may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributors:
    Pierre-Gildas MILLON <pgmillon@nuxeo.com>
"""

import re

from jira.client import JIRA
from nxtools import ServiceContainer
from nxtools.hooks.services import AbstractService


@ServiceContainer.service
class JiraService(AbstractService):

    def __init__(self):
        if "basic" == self.config("auth_type"):
            self.__jira_client = JIRA(self.config("url"),
                                      basic_auth=(self.config("basic_username"), self.config("basic_password")))

    def get_issue(self, id):
        """
        :rtype: jira.resources.Issue
        """
        return self.__jira_client.issue(id)

    def get_issue_id_from_branch(self, branch_name):
        matches = re.compile("[a-z]+-([A-Z]+-[0-9]+)-.*").match(branch_name)
        if matches:
            return matches.group(1)
        return None
