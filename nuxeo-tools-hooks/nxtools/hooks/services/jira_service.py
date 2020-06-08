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
import logging

from cachecontrol.adapter import CacheControlAdapter
from cachecontrol.heuristics import BaseHeuristic
from datetime import datetime, timedelta
from email.utils import parsedate, formatdate
from jira.client import JIRA
from jira.exceptions import JIRAError
from nxtools import ServiceContainer
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services import AbstractService

log = logging.getLogger(__name__)


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
        self.__jira_client = None
        # NB: the anonymous authentication will depend on any potential introspection from the Jira client logics
        # (as it can seamlesssly retrieve authentication information from a .netrc file for instance)
        self.__anonymous_jira_client = None
        if "basic" == self.config("auth_type"):
            self.__jira_client = JiraClient(self.config("url"),
                                            basic_auth=(self.config("basic_username"), self.config("basic_password")))
            self.__anonymous_jira_client = JiraClient(self.config("url"))
        elif self.config("url"):
            self.__jira_client = JiraClient(self.config("url"))
            self.__anonymous_jira_client = self.__jira_client

    @property
    def jira_regex(self):
        return re.compile(self.config("jira_regex", r"\b([A-Z]+-\d+)\b"), re.I)

    def get_issue(self, id, fields=None):
        """
        :rtype: jira.resources.Issue
        """
        if self.__jira_client is not None:
            try:
                return self.__jira_client.issue(id, fields)
            except Exception as e:
                log.debug('get_issue: %s', e)
                return None
        return None

    def get_issue_anonymous(self, id, fields=None):
        """
        :rtype: jira.resources.Issue
        """
        if self.__anonymous_jira_client is not None:
            try:
                return self.__anonymous_jira_client.issue(id, fields)
            except Exception as e:
                log.debug('get_issue_anonymous: %s', e)
                return None
        return None

    def get_issue_id_from_branch(self, branch_name):
        matches = self.jira_regex.match(branch_name)
        if matches:
            return matches.group(1)
        return None

    def get_issue_ids_from(self, text):
        res = []
        for match in self.jira_regex.finditer(text):
            ticket = match.group(1).upper()
            if ticket not in res:
                res.append(ticket)
        return res

    def get_issue_ids_from_pullrequest(self, pull_request):
        keys = []
        jira_main_key = self.get_issue_id_from_branch(pull_request.branch)
        if jira_main_key:
            keys.append(jira_main_key)

        commits = pull_request.gh_object.get_commits()
        for commit in commits:
            ckeys = self.get_issue_ids_from(commit.commit.message)
            for key in ckeys:
                keys.append(key) if key not in keys else None

        return keys

    def github_notify(self, keys, pull_request):
        if not self.config('create_link_to_pullrequest', False):
            return
        title = "PR for %s: #%s" % (pull_request.gh_object.base.ref, pull_request.pull_number)
        url = pull_request.gh_object.html_url
        links = []
        for key in keys:
            links.append(self.create_pullrequest_link(key, url, title))
        self.create_pullrequest_links(links)

    def create_pullrequest_link(self, key, url, title):
        return {
            "id": key,
            "uid": "ghpr=%s" %url,
            "relationship": "Is referenced in",
            "destination": {
                "url": url,
                "title": title,
                "icon": {
                    "url16x16": "https://github.com/favicon.ico",
                    "title": title
                },
            },
            "application": {
                "type": "com.nuxeo.nuxeo-tools-hooks",
                "name": "Captain Hook"
            }
        }

    def create_pullrequest_links(self, links):
        if self.__jira_client is not None:
            for link in links:
                try:
                    self.__jira_client.add_remote_link(
                        link["id"], link["destination"], globalId=link["uid"],
                        application=link["application"], relationship=link["relationship"])
                except Exception as e:
                    # ignore: issue could not exist for instance
                    log.debug('create_pullrequest_links: %s', e)
                    continue

