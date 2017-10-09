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
import calendar
from datetime import datetime, timedelta

from cachecontrol.adapter import CacheControlAdapter
from cachecontrol.heuristics import BaseHeuristic
from email.utils import parsedate, formatdate
from jira.client import JIRA
from nxtools import ServiceContainer
from nxtools.hooks.services import AbstractService


class OneDayHeuristic(BaseHeuristic):

    def update_headers(self, response):
        date = parsedate(response.headers['date'])
        expires = datetime(*date[:6]) + timedelta(days=1)

        return {
            'expires': formatdate(calendar.timegm(expires.timetuple())),
            'cache-control': 'public',
        }

    def warning(self, response):
        msg = 'Automatically cached! Response is Stale.'
        return '110 - "%s"' % msg


class JiraClient(JIRA):

    def __init__(self, server=None, options=None, basic_auth=None, oauth=None, jwt=None, kerberos=False, validate=False,
                 get_server_info=True, async=False, logging=True, max_retries=3, proxies=None):
        super(JiraClient, self).__init__(server, options, basic_auth, oauth, jwt, kerberos, validate, get_server_info,
                                         async, logging, max_retries, proxies)

        cacheControl = CacheControlAdapter(heuristic=OneDayHeuristic())

        self._session.mount('http://', cacheControl)
        self._session.mount('https://', cacheControl)
        self._session.headers.pop('cache-control')


@ServiceContainer.service
class JiraService(AbstractService):
    def __init__(self):
        if "basic" == self.config("auth_type"):
            self.__jira_client = JiraClient(self.config("url"),
                                            basic_auth=(self.config("basic_username"), self.config("basic_password")))

    def get_issue(self, id, fields=None):
        """
        :rtype: jira.resources.Issue
        """
        return self.__jira_client.issue(id, fields)

    def get_issue_id_from_branch(self, branch_name):
        matches = re.compile("[a-z]+-([A-Z]+-[0-9]+)-.*").match(branch_name)
        if matches:
            return matches.group(1)
        return None
