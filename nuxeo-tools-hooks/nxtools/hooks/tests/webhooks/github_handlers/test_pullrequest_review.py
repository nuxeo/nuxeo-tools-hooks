# -*- coding: utf-8 -*-
"""
(C) Copyright 2016-2019 Nuxeo SA (http://nuxeo.com/) and contributors.

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
    jcarsique
"""
import json

from github.PullRequest import PullRequest
from github.Commit import Commit
from jira.resources import Issue
from mock.mock import patch
from nxtools import services
from nxtools.hooks.endpoints.webhook.github_handlers.pull_request import GithubStorePullRequestHandler
from nxtools.hooks.entities.github_entities import PullRequestEvent
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.tests.webhooks.github_handlers import GithubHookHandlerTest


class MockPullRequest(PullRequest):

    class MockedPaginatedList(list):
        @property
        def reversed(self):
            self.reverse()
            return self

    def __init__(self, pr, commits):
        PullRequest.__init__(self, None, {}, pr, True)
        self._commits = commits
        self._comment = None

    def get_commits(self):
        res = MockPullRequest.MockedPaginatedList()
        for commit in self._commits:
            res.append(Commit(None, {}, commit, True))
        return res

    def create_issue_comment(self, comment):
        self._comment = comment


class GithubReviewPullRequestHandlerTest(GithubHookHandlerTest):

    def setUp(self):
        super(GithubReviewPullRequestHandlerTest, self).setUp()
        services.get(DatabaseService).connect()

    def tearDown(self):
        super(GithubReviewPullRequestHandlerTest, self).tearDown()
        StoredPullRequest.drop_collection()

    @property
    def handler(self):
        """
        :rtype: nxtools.hooks.endpoints.webhook.github_handlers.pull_request.GithubStorePullRequestHandler
        """
        return services.get(GithubStorePullRequestHandler)

    @property
    def config(self):
        """
        :rtype: nxtools.hooks.services.config.Config
        """
        return services.get(Config)

    def test_open_pull_request(self):
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload:
            body = self.get_json_body_from_payload(payload)
        event = PullRequestEvent(None, None, body, True)
        self.assertEqual(body["action"], event.action)
        self.assertEqual(body["number"], event.number)
        self.assertEqual(body["pull_request"]["head"]["ref"], event.pull_request.head.ref)
        self.assertEqual(body["pull_request"]["head"]["sha"], event.pull_request.head.sha)
        self.assertEqual(body["repository"]["name"], event.repository.name)

    def mock_get_pull(self, id):
        return self.mocks.pr

    def mock_get_issue(self, id, fields=None):
        if id == "NXBT-3308":
            raw = {
                'key': 'NXBT-3308',
                'fields': {
                    'summary': "test summary for GH comment",
                }
            }
            return Issue(None, None, raw=raw)
        return None

    def mock_create_jira_links(self, links):
        self.mocks.jira_links.extend(links)

    def setup_patches(self):
        patchers = [
            patch("nxtools.hooks.services.jira_service.JiraService.get_issue", self.mock_get_issue),
            patch("nxtools.hooks.services.jira_service.JiraService.get_issue_anonymous", self.mock_get_issue),
            patch("nxtools.hooks.services.jira_service.JiraService.create_pullrequest_links", self.mock_create_jira_links),
        ]
        [patcher.start() for patcher in patchers]
        [self.addCleanup(patcher.stop) for patcher in patchers]

    def setup_services_config(self):
        self.config._config.set("GithubReviewService", "active", "true")
        self.config._config.set("JiraService", "create_link_to_pullrequest", "true")

    def test_store_pull_request_trigger_review(self):
        self.setup_patches()
        self.setup_services_config()
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload, \
            GithubHookHandlerTest.payload_file('github_pullrequest') as prp, \
            GithubHookHandlerTest.payload_file('github_pullrequest_commits') as prc:
            body = self.get_json_body_from_payload(payload)
            pr = self.get_json_body_from_payload(prp)
            commits = self.get_json_body_from_payload(prc)
            self.mocks.pr = MockPullRequest(pr, commits)
            self.mocks.organization.get_repo.return_value.get_pull = self.mock_get_pull
            self.mocks.jira_links = []

            self.handler._do_handle(body)
            self.assertEqual("View issues in JIRA:\n" +
                             "- [NXP-20340](https://jira.nuxeo.com/browse/NXP-20340)\n" +
                             "- [NXBT-3308](https://jira.nuxeo.com/browse/NXBT-3308)", self.mocks.pr._comment)

            self.assertEqual(2, len(self.mocks.jira_links))
            link = {
                "id": "NXP-20340",
                "uid": "ghpr=https://github.com/nuxeo/nuxeo/pull/210",
                "relationship": "Is referenced in",
                "destination": {
                    "url": "https://github.com/nuxeo/nuxeo/pull/210",
                    "title": "PR for 6.0: #210",
                    "icon": {
                        "url16x16": "https://github.com/favicon.ico",
                        "title": "PR for 6.0: #210"
                    },
                },
                "application": {
                    "type": "com.nuxeo.nuxeo-tools-hooks",
                    "name": "Captain Hook"
                }
            }
            self.assertDictEqual(link, self.mocks.jira_links[0])
            link["id"] = "NXBT-3308"
            self.assertDictEqual(link, self.mocks.jira_links[1])

            # check verbosity setting
            self.config._config.set("GithubReviewService", "include_jira_summary", "true")
            self.handler._do_handle(body)
            self.assertEqual("View issues in JIRA:\n" +
                             "- [NXP-20340](https://jira.nuxeo.com/browse/NXP-20340)\n" +
                             "- [NXBT-3308](https://jira.nuxeo.com/browse/NXBT-3308): test summary for GH comment", self.mocks.pr._comment)

    def test_store_pull_request_trigger_review_private(self):
        self.setup_patches()
        self.setup_services_config()
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload, \
            GithubHookHandlerTest.payload_file('github_pullrequest') as prp, \
            GithubHookHandlerTest.payload_file('github_pullrequest_commits') as prc:
            body = self.get_json_body_from_payload(payload)
            body["repository"]["private"] = True
            pr = self.get_json_body_from_payload(prp)
            commits = self.get_json_body_from_payload(prc)
            self.mocks.pr = MockPullRequest(pr, commits)
            self.mocks.organization.get_repo.return_value.get_pull = self.mock_get_pull
            self.mocks.jira_links = []

            self.handler._do_handle(body)
            self.assertEqual(None, self.mocks.pr._comment)
            self.assertEqual(0, len(self.mocks.jira_links))
